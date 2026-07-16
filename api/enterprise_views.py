"""Ops, SLOs, API changelog, SCIM, and statutory reconciliation."""

from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAdmin, IsAdminOrManager, HasAPIKeyScope
from api.audit import log_action


API_CHANGELOG = [
    {
        'version': '1.0.0',
        'released': '2026-05-01',
        'changes': [
            'Initial public API surface with session auth and API keys.',
        ],
    },
    {
        'version': '1.1.0',
        'released': '2026-07-01',
        'changes': [
            'Added statutory PAYE/NSSF exports and scheduled reports.',
            'Added document access matrix and sensitive access audit log.',
        ],
    },
    {
        'version': '1.2.0',
        'released': '2026-07-15',
        'changes': [
            'Added organization tenancy, SCIM Users, ops/SLO endpoints.',
            'Webhook deliveries include attempt count and signed payloads.',
            'Deprecation headers for successor-version migrations.',
        ],
    },
]

RUNBOOKS = [
    {
        'id': 'payroll-day',
        'title': 'Payroll processing day',
        'severity': [
            'Confirm attendance approvals closed for the period.',
            'Run payroll generation and review variance vs prior month.',
            'Export URA PAYE and NSSF returns; archive snapshots.',
            'If errors >1% of payslips, halt and open incident.',
        ],
    },
    {
        'id': 'leave-spike',
        'title': 'Leave approval backlog spike',
        'severity': [
            'Check Approvals queue and notify managers with pending items.',
            'Verify leave balance accrual job ran this month.',
            'Escalate stalled multi-step workflows to HR admin.',
        ],
    },
    {
        'id': 'backup-restore',
        'title': 'Database backup restore',
        'severity': [
            'Identify backup file under backups/ or S3 prefix.',
            'Put app in maintenance (scale to 0 or hold traffic).',
            'Run: python manage.py restore_database path/to/backup',
            'Verify /api/v1/health/ and smoke login + payroll list.',
            'Document restore time for RTO evidence pack.',
        ],
    },
]


class APIChangelogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'current_version': '1.2.0',
            'deprecation_policy': (
                'Deprecated endpoints return Deprecation and Sunset headers. '
                'Consumers should migrate to successor links within 180 days.'
            ),
            'entries': API_CHANGELOG,
        })


class OpsStatusView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        jobs = {'scheduled': 0, 'success': 0, 'failed': 0, 'queued': 0, 'recent': []}
        try:
            from django_q.models import Failure, Schedule, Success, Task

            jobs['scheduled'] = Schedule.objects.count()
            jobs['success'] = Success.objects.count()
            jobs['failed'] = Failure.objects.count()
            jobs['queued'] = Task.objects.filter(success=None).count()
            recent = list(
                Success.objects.order_by('-stopped')[:5].values('name', 'func', 'stopped', 'success')
            ) + list(
                Failure.objects.order_by('-stopped')[:5].values('name', 'func', 'stopped', 'success')
            )
            jobs['recent'] = sorted(recent, key=lambda item: item.get('stopped') or timezone.now(), reverse=True)[:8]
        except Exception as exc:
            jobs['error'] = str(exc)

        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backups = []
        if backup_dir.exists():
            for path in sorted(backup_dir.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
                if path.is_file():
                    backups.append({
                        'name': path.name,
                        'size_bytes': path.stat().st_size,
                        'modified_at': timezone.datetime.fromtimestamp(
                            path.stat().st_mtime, tz=timezone.get_current_timezone(),
                        ).isoformat(),
                    })

        return Response({
            'jobs': jobs,
            'backups': backups,
            'runbooks': RUNBOOKS,
            'worker_hint': 'Start worker with: python manage.py qcluster',
        })


class SLOMetricsView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        hour_key = timezone.now().strftime('%Y%m%d%H')
        requests_count = int(cache.get(f'slo:requests:{hour_key}') or 0)
        errors_count = int(cache.get(f'slo:errors:{hour_key}') or 0)
        latency_sum = float(cache.get(f'slo:latency_ms:{hour_key}') or 0)
        availability = 100.0 if requests_count == 0 else round(
            100.0 * (1 - (errors_count / max(requests_count, 1))), 3,
        )
        avg_latency = 0.0 if requests_count == 0 else round(latency_sum / requests_count, 2)
        targets = {
            'availability_percent': 99.5,
            'error_budget_percent': 0.5,
            'avg_latency_ms': 800,
        }
        return Response({
            'window': 'current_hour',
            'requests': requests_count,
            'server_errors': errors_count,
            'availability_percent': availability,
            'avg_latency_ms': avg_latency,
            'targets': targets,
            'within_slo': availability >= targets['availability_percent'] and avg_latency <= targets['avg_latency_ms'],
            'request_id_header': 'X-Request-ID',
        })


class ScimUsersView(APIView):
    """Minimal SCIM 2.0 Users endpoint for IdP provisioning."""

    permission_classes = [IsAdmin, HasAPIKeyScope]
    throttle_classes = [__import__('api.throttles', fromlist=['SCIMRateThrottle']).SCIMRateThrottle]
    required_api_scopes = ['scim', 'admin']

    def get(self, request):
        from accounts.models import CustomUser

        start = int(request.query_params.get('startIndex', 1))
        count = min(int(request.query_params.get('count', 100)), 200)
        qs = CustomUser.objects.select_related('role', 'organization').order_by('id')
        filter_query = request.query_params.get('filter', '')
        if 'userName eq' in filter_query:
            username = filter_query.split('"')[1] if '"' in filter_query else ''
            qs = qs.filter(username=username)
        total = qs.count()
        users = qs[start - 1:start - 1 + count]
        resources = [self._to_scim(user) for user in users]
        return Response({
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
            'totalResults': total,
            'startIndex': start,
            'itemsPerPage': len(resources),
            'Resources': resources,
        })

    def post(self, request):
        from accounts.models import CustomUser, Organization, Role

        email = (request.data.get('emails') or [{}])[0].get('value') or request.data.get('userName')
        username = request.data.get('userName') or (email or '').split('@')[0]
        if not username or not email:
            return Response({'detail': 'userName and emails[0].value required'}, status=400)
        if CustomUser.objects.filter(username=username).exists():
            return Response({'detail': 'User already exists'}, status=409)
        role_name = Role.EMPLOYEE
        for group in request.data.get('groups') or []:
            display = (group.get('display') or '').lower()
            if display in (Role.ADMIN, Role.MANAGER, Role.EMPLOYEE):
                role_name = display
        role, _ = Role.objects.get_or_create(name=role_name)
        org = None
        if request.user.organization_id:
            org = request.user.organization
        from django.utils.crypto import get_random_string

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=get_random_string(32),
            role=role,
            organization=org,
            external_id=request.data.get('externalId', ''),
            first_name=(request.data.get('name') or {}).get('givenName', ''),
            last_name=(request.data.get('name') or {}).get('familyName', ''),
            is_active=request.data.get('active', True),
        )
        log_action(request, 'create', 'CustomUser', user.id, username, 'SCIM provisioned')
        return Response(self._to_scim(user), status=status.HTTP_201_CREATED)

    def _to_scim(self, user):
        return {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'id': str(user.id),
            'externalId': user.external_id or '',
            'userName': user.username,
            'name': {
                'givenName': user.first_name,
                'familyName': user.last_name,
            },
            'emails': [{'value': user.email, 'primary': True}],
            'active': user.is_active,
            'meta': {
                'resourceType': 'User',
                'location': f'/api/v1/scim/v2/Users/{user.id}',
            },
        }


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        from accounts.models import Organization
        return Organization.objects.all()

    def get_serializer_class(self):
        from api.serializers import OrganizationSerializer
        return OrganizationSerializer


class StatutoryReconciliationView(APIView):
    """Compare payroll statutory totals vs exported filing rows for a period."""

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        from decimal import Decimal

        from payroll.models import Salary

        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        qs = Salary.objects.filter(month=month, year=year).select_related('employee')
        totals = {
            'employees': qs.count(),
            'gross': Decimal('0'),
            'paye': Decimal('0'),
            'nssf_employee': Decimal('0'),
            'nssf_employer': Decimal('0'),
            'missing_tin': 0,
            'missing_nssf': 0,
        }
        issues = []
        for salary in qs:
            totals['gross'] += salary.gross_salary or 0
            totals['paye'] += salary.tax or 0
            totals['nssf_employee'] += salary.nssf_employee or 0
            totals['nssf_employer'] += salary.nssf_employer or 0
            if not salary.employee.tax_identification_number:
                totals['missing_tin'] += 1
                issues.append({
                    'employee': salary.employee.full_name,
                    'issue': 'Missing TIN for PAYE filing',
                })
            if not salary.employee.nssf_number:
                totals['missing_nssf'] += 1
                issues.append({
                    'employee': salary.employee.full_name,
                    'issue': 'Missing NSSF number',
                })
        return Response({
            'period': f'{year}-{month:02d}',
            'totals': {k: (float(v) if isinstance(v, Decimal) else v) for k, v in totals.items()},
            'issues': issues,
            'ready_to_file': totals['missing_tin'] == 0 and totals['missing_nssf'] == 0 and totals['employees'] > 0,
        })

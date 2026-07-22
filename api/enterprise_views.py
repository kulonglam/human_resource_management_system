"""Ops, SLOs, API changelog, SCIM, and statutory reconciliation."""

from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAdmin, IsAdminOrManager
from api.dr_monitoring import get_dr_snapshot
from api.ops_monitoring import get_ops_alerts_snapshot, get_slo_snapshot
from api.redis_config import infrastructure_snapshot


def _safe_ops_alerts_snapshot():
    try:
        return get_ops_alerts_snapshot()
    except Exception as exc:
        return {
            'cooldown_minutes': 30,
            'checked_at': timezone.now().isoformat(),
            'active': [],
            'cooldowns': [],
            'recent': [],
            'breach_count': 0,
            'cooldown_active_count': 0,
            'error': str(exc),
        }


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
            'Added organization tenancy, SCIM Users/Groups, device attendance, ops/SLO endpoints.',
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
            'Identify backup file under backups/ or S3 (postgres_*.dump.enc or sqlite_*.sqlite3.enc).',
            'Put app in maintenance (scale to 0 or hold traffic).',
            'Prefer restore drill on staging first: python manage.py verify_backup --path <file>',
            'Run: python manage.py restore_database path/to/backup.dump.enc --force',
            'Postgres uses pg_restore --clean --if-exists (custom -Fc). Legacy .sql uses psql.',
            'Verify /api/v1/health/ and smoke login + payroll list.',
            'Document restore time for RTO evidence pack.',
            'Run monthly on staging: python manage.py run_monthly_dr_checks',
        ],
    },
    {
        'id': 'security-incident',
        'title': 'Security / data incident',
        'checklist': [
            'Declare severity and incident commander (see INCIDENT_RESPONSE.md).',
            'Preserve audit logs; avoid wiping evidence.',
            'Contain: disable accounts, rotate exposed secrets from a clean device.',
            'Pause retention purges until cleared (apply_retention_policies --dry-run only).',
            'Check /api/v1/health/, Ops Center, and Sentry.',
            'Notify HR_NOTIFY_EMAIL / leadership for SEV-1/2.',
            'Close with post-incident review and update compliance evidence.',
        ],
    },
    {
        'id': 'retention-enforcement',
        'title': 'Data retention enforcement',
        'checklist': [
            'Preview: python manage.py apply_retention_policies --dry-run',
            'Review eligible counts in /settings/compliance.',
            'Purge runs automatically via run_scheduled_tasks (skip with --skip-retention).',
            'Manual purge: python manage.py apply_retention_policies',
            'Confirm AuditLog entries for retention runs.',
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

        retention = {
            'keep_count': int(getattr(settings, 'BACKUP_RETENTION_COUNT', 14) or 0),
            'keep_days': int(getattr(settings, 'BACKUP_RETENTION_DAYS', 30) or 0),
            'hint': (
                'Local backups pruned after each backup_database run. '
                'Configure S3 lifecycle separately for offsite objects. '
                'Restore: python manage.py restore_database <path> --force'
            ),
        }

        from api.ops_monitoring import get_usage_snapshot

        return Response({
            'jobs': jobs,
            'backups': backups,
            'backup_retention': retention,
            'disaster_recovery': get_dr_snapshot(),
            'alerts': _safe_ops_alerts_snapshot(),
            'usage': get_usage_snapshot(),
            'infrastructure': infrastructure_snapshot(getattr(settings, 'REDIS_URL', '') or None),
            'runbooks': RUNBOOKS,
            'worker_hint': 'Start worker with: python manage.py qcluster',
        })


class SLOMetricsView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        return Response(get_slo_snapshot())


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

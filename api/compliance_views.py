from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.access_control import can_access_employee, get_user_accessible_employees
from accounts.models import AuditLog
from api.audit import log_action
from api.compliance_export import anonymize_employee, build_employee_data_export, export_json_response
from api.compliance_serializers import (
    ComplianceEvidencePackSerializer,
    DataRetentionPolicySerializer,
    RetentionPreviewSerializer,
    VulnerabilityFindingSerializer,
)
from api.permissions import IsAdmin
from api.report_exports import export_rows_csv, export_rows_xlsx
from compliance.models import ComplianceEvidencePack, DataRetentionPolicy, VulnerabilityFinding
from compliance.retention import apply_all_retention_policies, preview_retention
from employees.models import Employee


class DataRetentionPolicyViewSet(viewsets.ModelViewSet):
    queryset = DataRetentionPolicy.objects.all()
    serializer_class = DataRetentionPolicySerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'patch', 'head', 'options']

    def perform_update(self, serializer):
        policy = serializer.save()
        log_action(
            self.request, 'update', 'DataRetentionPolicy', policy.pk,
            policy.get_category_display(),
            f'retention_days={policy.retention_days}, active={policy.is_active}',
        )


class ComplianceEvidencePackViewSet(viewsets.ModelViewSet):
    queryset = ComplianceEvidencePack.objects.all()
    serializer_class = ComplianceEvidencePackSerializer
    permission_classes = [IsAdmin]


class VulnerabilityFindingViewSet(viewsets.ModelViewSet):
    queryset = VulnerabilityFinding.objects.all()
    serializer_class = VulnerabilityFindingSerializer
    permission_classes = [IsAdmin]


class RetentionPreviewView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        previews = []
        for policy in DataRetentionPolicy.objects.all():
            previews.append({
                'category': policy.category,
                'category_label': policy.get_category_display(),
                'retention_days': policy.retention_days,
                'eligible_count': preview_retention(policy) if policy.is_active else 0,
            })
        serializer = RetentionPreviewSerializer(previews, many=True)
        return Response(serializer.data)


class RetentionRunView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        dry_run = str(request.data.get('dry_run', 'false')).lower() in ('1', 'true', 'yes')
        results = apply_all_retention_policies(dry_run=dry_run)
        total = sum(item['purged'] for item in results)
        if not dry_run and total:
            log_action(
                request, 'delete', 'DataRetentionPolicy', None,
                'Retention purge',
                f'Purged {total} record(s) across {len(results)} categories',
            )
        return Response({
            'dry_run': dry_run,
            'results': results,
            'total_purged': total,
        })


class GDPRDataExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id=None):
        if employee_id is None:
            try:
                employee = Employee.objects.get(email=request.user.email)
            except Employee.DoesNotExist:
                return Response(
                    {'detail': 'No employee profile linked to your account.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            if not request.user.is_admin and not request.user.is_manager:
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            employee = Employee.objects.filter(pk=employee_id).first()
            if not employee:
                return Response({'detail': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
            if not can_access_employee(request.user, employee):
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        payload = build_employee_data_export(employee, request)
        log_action(
            request, 'export', 'Employee', employee.pk, employee.full_name,
            'GDPR subject access export',
        )
        download = request.query_params.get('download', '').lower() in ('1', 'true', 'yes')
        if download:
            return export_json_response(payload, f'gdpr_export_{employee.pk}')
        return Response(payload)


class GDPRErasureView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, employee_id):
        employee = Employee.objects.filter(pk=employee_id).first()
        if not employee:
            return Response({'detail': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)

        confirm = request.data.get('confirm')
        if confirm != employee.email:
            return Response(
                {'detail': 'Confirmation failed. Pass confirm=<employee email>.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name_before = employee.full_name
        anonymize_employee(employee)
        log_action(
            request, 'delete', 'Employee', employee.pk, name_before,
            'GDPR erasure — personal data anonymized',
        )
        return Response({
            'detail': 'Employee personal data anonymized.',
            'employee_id': employee.pk,
        })


def audit_log_export_response(request):
    qs = AuditLog.objects.select_related('user').order_by('-timestamp')

    start = request.query_params.get('start')
    end = request.query_params.get('end')
    action = request.query_params.get('action')
    if start:
        qs = qs.filter(timestamp__date__gte=start)
    if end:
        qs = qs.filter(timestamp__date__lte=end)
    if action:
        qs = qs.filter(action=action)

    columns = [
        {'key': 'timestamp', 'label': 'Timestamp'},
        {'key': 'username', 'label': 'User'},
        {'key': 'action', 'label': 'Action'},
        {'key': 'model_name', 'label': 'Model'},
        {'key': 'object_id', 'label': 'Object ID'},
        {'key': 'object_description', 'label': 'Object'},
        {'key': 'details', 'label': 'Details'},
        {'key': 'ip_address', 'label': 'IP Address'},
    ]
    rows = [
        {
            'timestamp': log.timestamp.isoformat(),
            'username': log.user.username if log.user else '',
            'action': log.action,
            'model_name': log.model_name,
            'object_id': log.object_id or '',
            'object_description': log.object_description,
            'details': log.details,
            'ip_address': log.ip_address or '',
        }
        for log in qs[:10000]
    ]

    path = request.path.rstrip('/')
    if path.endswith('.xlsx'):
        export_format = 'xlsx'
    elif path.endswith('.csv'):
        export_format = 'csv'
    else:
        export_format = request.query_params.get('export_as', 'csv').lower()
    log_action(
        request, 'export', 'AuditLog', None, 'Audit log export',
        f'format={export_format}, rows={len(rows)}',
    )
    if export_format == 'xlsx':
        return export_rows_xlsx(rows, columns, 'audit_log', 'Audit Log')
    return export_rows_csv(rows, columns, 'audit_log')

from accounts.models import SensitiveDataAccessLog


SENSITIVE_EMPLOYEE_FIELDS = (
    'account_number', 'bank', 'salary',
    'national_id_number', 'tax_identification_number', 'nssf_number',
)


def log_sensitive_employee_access(request, employee, fields_accessed=None):
    if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
        return
    SensitiveDataAccessLog.objects.create(
        user=request.user,
        employee=employee,
        fields_accessed=fields_accessed or list(SENSITIVE_EMPLOYEE_FIELDS),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
    )

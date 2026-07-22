from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Organization(models.Model):
    """Tenant organization for multi-company deployments."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Role(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
    ]
    PERMISSION_PAYROLL_VIEW = 'payroll.view'
    PERMISSION_PAYROLL_MANAGE = 'payroll.manage'
    PERMISSION_REPORTS_MANAGE = 'reports.manage'
    PERMISSION_SENSITIVE_VIEW = 'sensitive.view'
    PERMISSION_ATTENDANCE_APPROVE = 'attendance.approve'
    PERMISSION_DOCUMENTS_MANAGE = 'documents.manage'

    ALL_PERMISSIONS = [
        PERMISSION_PAYROLL_VIEW,
        PERMISSION_PAYROLL_MANAGE,
        PERMISSION_REPORTS_MANAGE,
        PERMISSION_SENSITIVE_VIEW,
        PERMISSION_ATTENDANCE_APPROVE,
        PERMISSION_DOCUMENTS_MANAGE,
    ]

    DEFAULT_PERMISSIONS = {
        ADMIN: ALL_PERMISSIONS,
        MANAGER: [
            PERMISSION_PAYROLL_VIEW,
            PERMISSION_REPORTS_MANAGE,
            PERMISSION_SENSITIVE_VIEW,
            PERMISSION_ATTENDANCE_APPROVE,
        ],
        EMPLOYEE: [],
    }

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    permissions = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name

    def resolved_permissions(self):
        if self.permissions:
            return list(self.permissions)
        return list(self.DEFAULT_PERMISSIONS.get(self.name, []))


class CustomUser(AbstractUser):
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True
    )
    email = models.EmailField(unique=True)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)
    managed_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_by_users',
        help_text='Department scope for managers without a linked employee profile.',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    external_id = models.CharField(
        max_length=128, blank=True, db_index=True,
        help_text='SCIM / IdP external identifier.',
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role and self.role.name == Role.ADMIN

    @property
    def is_manager(self):
        return self.role and self.role.name == Role.MANAGER


class AuditLog(models.Model):
    """Track all important actions performed in the system."""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='other')
    model_name = models.CharField(max_length=100, help_text="Name of the model/object affected")
    object_id = models.IntegerField(null=True, blank=True, help_text="ID of the affected object")
    object_description = models.CharField(
        max_length=255, blank=True, help_text="Description of the affected object"
    )
    details = models.TextField(blank=True, help_text="Additional details about the action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ('-timestamp',)
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.model_name} by {self.user} on {self.timestamp}"


class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('approval', 'Approval'),
        ('leave', 'Leave'),
        ('expense', 'Expense'),
        ('recruitment', 'Recruitment'),
        ('document', 'Document'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='notifications',
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'{self.title} → {self.user.username}'


class SensitiveDataAccessLog(models.Model):
    """Audit trail when payroll or PII fields are viewed."""

    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='sensitive_access_logs',
    )
    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE, related_name='sensitive_access_logs',
    )
    fields_accessed = models.JSONField(default=list)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    accessed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ('-accessed_at',)

    def __str__(self):
        return f'{self.user} viewed {self.employee} at {self.accessed_at}'


class OpsAlertEvent(models.Model):
    """Durable ops alert history (survives cache/Redis restarts)."""

    key = models.CharField(max_length=64, db_index=True)
    level = models.CharField(max_length=16, default='warning')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    outcome = models.CharField(max_length=20, default='emitted')  # emitted | suppressed
    payload = models.JSONField(default=dict, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ops_alert_events',
    )
    emitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ('-emitted_at',)
        indexes = [
            models.Index(fields=['key', '-emitted_at']),
        ]

    def __str__(self):
        return f'{self.key} ({self.outcome}) @ {self.emitted_at}'
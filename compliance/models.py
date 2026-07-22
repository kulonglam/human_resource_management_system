from django.db import models
from django.utils import timezone


class DataRetentionPolicy(models.Model):
    CATEGORY_CHOICES = [
        ('audit_logs', 'Audit logs'),
        ('webhook_deliveries', 'Webhook delivery history'),
        ('notifications', 'In-app notifications'),
        ('rejected_applications', 'Rejected job applications'),
    ]

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, unique=True)
    retention_days = models.PositiveIntegerField(
        help_text='Records older than this many days may be purged.',
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_purged_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Data retention policies'
        ordering = ('category',)

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f'{self.get_category_display()} ({self.retention_days} days, {status})'


class ComplianceEvidencePack(models.Model):
    """Artifacts for auditors (SOC2/ISO-style evidence index)."""

    CONTROL_CHOICES = [
        ('access_control', 'Access control'),
        ('encryption', 'Encryption at rest'),
        ('backup_restore', 'Backup & restore'),
        ('audit_logging', 'Audit logging'),
        ('data_retention', 'Data retention'),
        ('incident_response', 'Incident response'),
        ('vulnerability_mgmt', 'Vulnerability management'),
        ('penetration_testing', 'Penetration testing'),
        ('change_management', 'Change management'),
        ('availability_slo', 'Availability / SLO'),
        ('access_reviews', 'Access reviews'),
    ]

    control = models.CharField(max_length=40, choices=CONTROL_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    evidence_url = models.URLField(blank=True)
    owner = models.CharField(max_length=100, blank=True)
    last_reviewed_at = models.DateField(null=True, blank=True)
    next_review_at = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('ready', 'Ready'), ('gap', 'Gap')],
        default='draft',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['control', 'title']

    def __str__(self):
        return f'{self.get_control_display()} — {self.title}'


class VulnerabilityFinding(models.Model):
    """Tracked security findings with remediation SLAs."""

    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In progress'),
        ('resolved', 'Resolved'),
        ('accepted', 'Risk accepted'),
    ]
    SLA_DAYS = {'critical': 7, 'high': 14, 'medium': 30, 'low': 90}

    title = models.CharField(max_length=200)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    discovered_at = models.DateField(default=timezone.now)
    due_at = models.DateField(null=True, blank=True)
    resolved_at = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    remediation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-discovered_at', 'severity']

    def save(self, *args, **kwargs):
        if not self.due_at and self.severity in self.SLA_DAYS:
            from datetime import timedelta
            self.due_at = self.discovered_at + timedelta(days=self.SLA_DAYS[self.severity])
        super().save(*args, **kwargs)

    @property
    def sla_breached(self):
        if self.status in ('resolved', 'accepted') or not self.due_at:
            return False
        return timezone.now().date() > self.due_at

    def __str__(self):
        return f'[{self.severity}] {self.title}'

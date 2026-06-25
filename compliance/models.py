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

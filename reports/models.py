from django.db import models

from accounts.models import CustomUser


class SavedReport(models.Model):
    """Store saved report configurations for quick access."""

    REPORT_TYPES = [
        ('attendance', 'Attendance Report'),
        ('leave', 'Leave Report'),
        ('payroll', 'Payroll Report'),
        ('performance', 'Performance Report'),
        ('recruitment', 'Recruitment Report'),
        ('hr_analytics', 'HR Analytics'),
        ('employee', 'Employee Report'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    filters = models.JSONField(default=dict, help_text='Saved filter parameters')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False, help_text='Share with all users')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ReportSnapshot(models.Model):
    """Store snapshots of generated reports for historical tracking."""

    report_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    report_data = models.JSONField()
    filters_used = models.JSONField(default=dict)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f'{self.title} - {self.generated_at.date()}'


class ScheduledReport(models.Model):
    """Automated report delivery by email."""

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
    ]

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=SavedReport.REPORT_TYPES)
    filters = models.JSONField(default=dict)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    export_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='xlsx')
    recipient_emails = models.JSONField(default=list, help_text='List of email addresses')
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

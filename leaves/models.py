from django.db import models
from django.utils import timezone
from employees.models import Employee
import datetime


class Leave(models.Model):
    LEAVE_TYPES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='leaves'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.CharField(max_length=100, blank=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)

    @property
    def duration(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.status})"


class LeaveBalance(models.Model):
    """Tracks leave balance per employee per leave type per year."""
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='leave_balances'
    )
    leave_type = models.CharField(max_length=20, choices=Leave.LEAVE_TYPES)
    year = models.IntegerField(default=timezone.now().year)
    total_days = models.IntegerField(default=0, help_text="Total leave days allocated")
    used_days = models.FloatField(default=0, help_text="Days already used")
    pending_days = models.FloatField(default=0, help_text="Days in pending approval")
    
    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ('year', 'leave_type')

    @property
    def available_days(self):
        """Calculate available leave days."""
        return self.total_days - self.used_days - self.pending_days

    def __str__(self):
        return f"{self.employee.user.username} - {self.get_leave_type_display()} ({self.year})"

    def get_leave_type_display(self):
        return dict(Leave.LEAVE_TYPES).get(self.leave_type, self.leave_type)
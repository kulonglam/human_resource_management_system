from django.db import models

from accounts.models import CustomUser
from employees.models import Employee
from shifts.models import ShiftAssignment


class PublicHoliday(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField(unique=True)
    is_recurring = models.BooleanField(
        default=False,
        help_text='If true, holiday repeats annually on the same month/day.',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date']
        verbose_name_plural = 'Public holidays'

    def __str__(self):
        return f'{self.name} ({self.date})'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ]
    APPROVAL_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('import', 'Import'),
        ('timesheet', 'Timesheet'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='attendances',
    )
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    approval_status = models.CharField(
        max_length=10, choices=APPROVAL_STATUS_CHOICES, default='draft',
    )
    approved_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_attendances',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    shift_assignment = models.ForeignKey(
        ShiftAssignment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendance_records',
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.employee} — {self.date} ({self.status})'


class Timesheet(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='timesheets',
    )
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    regular_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    project_code = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_timesheets',
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.employee} — {self.date} ({self.status})'


class OvertimeRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='overtime_records',
    )
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_overtime',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.employee} — {self.date} ({self.hours}h)'

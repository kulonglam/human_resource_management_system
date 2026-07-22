from django.db import models

from accounts.models import CustomUser
from accounts.tenancy import organization_fk
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
    organization = organization_fk(related_name='public_holidays')

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
        ('device', 'Biometric / device'),
        ('mobile', 'Mobile'),
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


class AttendanceDevice(models.Model):
    """Registered biometric / RFID / mobile attendance terminal."""

    DEVICE_TYPES = [
        ('fingerprint', 'Fingerprint'),
        ('face', 'Face recognition'),
        ('rfid', 'RFID / badge'),
        ('mobile', 'Mobile app'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=120)
    device_code = models.SlugField(max_length=64, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='fingerprint')
    location = models.CharField(max_length=200, blank=True)
    organization = organization_fk(related_name='attendance_devices')
    is_active = models.BooleanField(default=True)
    token_prefix = models.CharField(max_length=12, unique=True, editable=False)
    token_hash = models.CharField(max_length=64, editable=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.device_code})'


class DevicePunch(models.Model):
    """Raw punch from a device or mobile offline sync."""

    PUNCH_TYPES = [
        ('in', 'Clock in'),
        ('out', 'Clock out'),
        ('auto', 'Auto'),
    ]

    device = models.ForeignKey(
        AttendanceDevice, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='punches',
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='device_punches',
    )
    badge_id = models.CharField(max_length=64, blank=True, db_index=True)
    punched_at = models.DateTimeField(db_index=True)
    punch_type = models.CharField(max_length=8, choices=PUNCH_TYPES, default='auto')
    source = models.CharField(max_length=20, default='device')  # device | mobile | offline_sync
    client_punch_id = models.CharField(
        max_length=64, blank=True, db_index=True,
        help_text='Idempotency key from mobile offline queue.',
    )
    raw_payload = models.JSONField(default=dict, blank=True)
    attendance = models.ForeignKey(
        Attendance, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='device_punches',
    )
    applied = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-punched_at']
        indexes = [
            models.Index(fields=['client_punch_id']),
        ]

    def __str__(self):
        return f'{self.badge_id or self.employee_id} @ {self.punched_at}'

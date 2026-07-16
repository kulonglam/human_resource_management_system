from django.db import models
from django.conf import settings

from accounts.fields import EncryptedCharField, EncryptedDecimalField
from departments.models import Department
from uuid import uuid4


class JobGrade(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    rank = models.PositiveIntegerField(default=1)
    minimum_salary = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    maximum_salary = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['rank', 'code']

    def __str__(self):
        return f'{self.code} — {self.name}'


class Position(models.Model):
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='positions')
    grade = models.ForeignKey(
        JobGrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='positions',
    )
    reports_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports',
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['department__name', 'title']

    def __str__(self):
        return f'{self.title} ({self.code})'


class Employee(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    EXIT_REASON_CHOICES = [
        ('resignation', 'Resignation'),
        ('termination', 'Termination'),
        ('retirement', 'Retirement'),
        ('contract_end', 'Contract End'),
        ('medical', 'Medical Grounds'),
        ('redundancy', 'Redundancy'),
        ('other', 'Other'),
    ]

    # Personal Information
    photo = models.ImageField(upload_to='employees/photos/', null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(max_length=125, unique=True)
    mobile = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    emergency_contact = models.CharField(max_length=30)
    language = models.CharField(max_length=10, default='English')
    national_id_number = EncryptedCharField()
    tax_identification_number = EncryptedCharField()
    nssf_number = EncryptedCharField()

    # Employment Information
    employee_number = models.CharField(max_length=30, unique=True, editable=False)
    job_title = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name='employees'
    )
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
    )
    position = models.ForeignKey(
        Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees',
    )
    grade = models.ForeignKey(
        JobGrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees',
    )
    supervisor = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members',
    )
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('permanent', 'Permanent'),
            ('fixed_term', 'Fixed Term'),
            ('temporary', 'Temporary'),
            ('intern', 'Intern'),
            ('consultant', 'Consultant'),
        ],
        default='permanent',
    )
    date_joined = models.DateField()
    probation_end_date = models.DateField(null=True, blank=True)
    work_location = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    # Banking / Payroll
    account_number = EncryptedCharField()
    bank = EncryptedCharField()
    salary = EncryptedDecimalField(blank=False, null=False)

    # Termination Information
    termination_date = models.DateField(null=True, blank=True, help_text="Employee exit date")
    exit_reason = models.CharField(
        max_length=20, 
        choices=EXIT_REASON_CHOICES, 
        null=True, 
        blank=True,
        help_text="Reason for employee termination"
    )
    exit_notes = models.TextField(blank=True, help_text="Additional notes about termination")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.employee_number:
            self.employee_number = f'EMP-{uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_terminated(self):
        """Check if employee has been terminated."""
        return self.termination_date is not None


class EmploymentContract(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(
        max_length=20,
        choices=[
            ('permanent', 'Permanent'),
            ('fixed_term', 'Fixed Term'),
            ('temporary', 'Temporary'),
            ('internship', 'Internship'),
            ('consultancy', 'Consultancy'),
        ],
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=16, decimal_places=2)
    status = models.CharField(
        max_length=15,
        choices=[('draft', 'Draft'), ('active', 'Active'), ('expired', 'Expired'), ('terminated', 'Terminated')],
        default='draft',
    )
    document = models.FileField(upload_to='employees/contracts/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.employee} — {self.get_contract_type_display()}'


class EmploymentHistory(models.Model):
    EVENT_CHOICES = [
        ('hire', 'Hire'),
        ('promotion', 'Promotion'),
        ('transfer', 'Transfer'),
        ('grade_change', 'Grade Change'),
        ('salary_change', 'Salary Change'),
        ('contract_change', 'Contract Change'),
        ('exit', 'Exit'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employment_history')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    effective_date = models.DateField()
    previous_position = models.ForeignKey(
        Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    new_position = models.ForeignKey(
        Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    previous_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    new_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    previous_grade = models.ForeignKey(
        JobGrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    new_grade = models.ForeignKey(
        JobGrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='employment_changes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date', '-created_at']

    def __str__(self):
        return f'{self.employee} — {self.get_event_type_display()} ({self.effective_date})'
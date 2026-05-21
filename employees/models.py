from django.db import models
from departments.models import Department

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
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=100)
    emergency_contact = models.CharField(max_length=11)
    language = models.CharField(max_length=10, default='English')

    # Employment Information
    job_title = models.CharField(max_length=20)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name='employees'
    )
    date_joined = models.DateField()
    is_active = models.BooleanField(default=True)

    # Banking / Payroll
    account_number = models.CharField(max_length=10)
    bank = models.CharField(max_length=25)
    salary = models.DecimalField(max_digits=16, decimal_places=2)

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

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_terminated(self):
        """Check if employee has been terminated."""
        return self.termination_date is not None
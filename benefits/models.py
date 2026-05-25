from django.db import models
from employees.models import Employee
from departments.models import Department

class Benefit(models.Model):
    BENEFIT_TYPE_CHOICES = [
        ('health', 'Health Insurance'),
        ('retirement', 'Retirement Plan'),
        ('education', 'Education Assistance'),
        ('wellness', 'Wellness Program'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    benefit_type = models.CharField(max_length=20, choices=BENEFIT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    provider = models.CharField(max_length=100, blank=True)
    cost_per_employee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employer_contribution = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_mandatory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    applicable_to_all = models.BooleanField(default=False)
    departments = models.ManyToManyField(Department, blank=True, related_name='benefits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Benefits'

    def __str__(self):
        return self.name


class EmployeeBenefit(models.Model):
    ENROLLMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employee_benefits')
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField()
    termination_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS_CHOICES, default='pending')
    plan_type = models.CharField(max_length=100, blank=True, help_text='e.g., Premium, Basic, Family')
    monthly_deduction = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    beneficiary_name = models.CharField(max_length=200, blank=True)
    beneficiary_relationship = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'benefit']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.employee} - {self.benefit.name}"

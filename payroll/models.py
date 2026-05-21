from django.db import models
from django.utils import timezone
from employees.models import Employee
from datetime import datetime

class Salary(models.Model):
    PAYMENT_FREQUENCY = [
        ('monthly', 'Monthly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('weekly', 'Weekly'),
    ]
    PAYMENT_METHOD = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='payroll_records'
    )
    month = models.PositiveIntegerField()   # 1–12
    year = models.PositiveIntegerField()
    basic_salary = models.DecimalField(max_digits=16, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=16, decimal_places=2, editable=False)
    payment_frequency = models.CharField(max_length=15, choices=PAYMENT_FREQUENCY, default='monthly')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD, default='bank_transfer')
    paid_on = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def save(self, *args, **kwargs):
        self.net_salary = self.basic_salary + self.allowances - self.deductions - self.tax
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.month}/{self.year} (Net: {self.net_salary})"

    @property
    def month_name(self):
        """Return month name."""
        return datetime(self.year, self.month, 1).strftime('%B')

    @property
    def total_earnings(self):
        """Total earnings = basic + allowances."""
        return self.basic_salary + self.allowances

    @property
    def total_deductions(self):
        """Total deductions = deductions + tax."""
        return self.deductions + self.tax
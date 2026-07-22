from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.tenancy import organization_fk
from employees.models import Employee
from datetime import datetime
from payroll.uganda import calculate_statutory_payroll


class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]

    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    organization = organization_fk(related_name='payroll_runs')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payroll_runs_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payroll_runs_approved',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('month', 'year', 'organization')
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{datetime(self.year, self.month, 1):%B %Y} payroll ({self.status})'

class Salary(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]
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
    payroll_run = models.ForeignKey(
        PayrollRun, on_delete=models.PROTECT, related_name='salary_records',
    )
    month = models.PositiveIntegerField()   # 1–12
    year = models.PositiveIntegerField()
    basic_salary = models.DecimalField(max_digits=16, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_benefits = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=16, decimal_places=2, editable=False, default=0)
    chargeable_income = models.DecimalField(max_digits=16, decimal_places=2, editable=False, default=0)
    tax = models.DecimalField(
        max_digits=16, decimal_places=2, editable=False, default=0,
        help_text='Uganda PAYE withheld for this payroll period.',
    )
    nssf_employee = models.DecimalField(max_digits=16, decimal_places=2, editable=False, default=0)
    nssf_employer = models.DecimalField(max_digits=16, decimal_places=2, editable=False, default=0)
    local_service_tax = models.DecimalField(max_digits=16, decimal_places=2, editable=False, default=0)
    net_salary = models.DecimalField(max_digits=16, decimal_places=2, editable=False)
    is_resident = models.BooleanField(default=True)
    is_secondary_employment = models.BooleanField(default=False)
    nssf_applicable = models.BooleanField(default=True)
    lst_applicable = models.BooleanField(default=True)
    payment_frequency = models.CharField(max_length=15, choices=PAYMENT_FREQUENCY, default='monthly')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD, default='bank_transfer')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    paid_on = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def save(self, *args, **kwargs):
        if not self.payroll_run_id:
            self.payroll_run, _ = PayrollRun.objects.get_or_create(month=self.month, year=self.year)
        if self.is_paid and self.status == 'draft':
            self.status = 'paid'
        self.gross_salary = self.basic_salary + self.allowances + self.taxable_benefits
        statutory = calculate_statutory_payroll(
            self.gross_salary,
            self.month,
            resident=self.is_resident,
            secondary_employment=self.is_secondary_employment,
            nssf_applicable=self.nssf_applicable,
            lst_applicable=self.lst_applicable,
        )
        self.chargeable_income = statutory['chargeable_income']
        self.tax = statutory['paye']
        self.nssf_employee = statutory['nssf_employee']
        self.nssf_employer = statutory['nssf_employer']
        self.local_service_tax = statutory['local_service_tax']
        self.net_salary = (
            self.gross_salary
            - self.deductions
            - self.tax
            - self.nssf_employee
            - self.local_service_tax
        )
        self.is_paid = self.status == 'paid'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.month}/{self.year} (Net: {self.net_salary})"

    @property
    def month_name(self):
        """Return month name."""
        return datetime(self.year, self.month, 1).strftime('%B')

    @property
    def total_earnings(self):
        return self.gross_salary

    @property
    def total_deductions(self):
        return self.deductions + self.tax + self.nssf_employee + self.local_service_tax
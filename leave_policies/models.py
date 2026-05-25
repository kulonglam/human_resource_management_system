from django.db import models
from employees.models import Employee
from departments.models import Department

class LeavePolicy(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('bereavement', 'Bereavement Leave'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    days_per_year = models.IntegerField()
    carryforward_allowed = models.BooleanField(default=False)
    carryforward_limit = models.IntegerField(blank=True, null=True, help_text='Maximum days to carry forward')
    description = models.TextField(blank=True)
    applicable_to_all = models.BooleanField(default=False)
    departments = models.ManyToManyField(Department, blank=True, related_name='leave_policies')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Leave Policies'

    def __str__(self):
        return self.name


class LeavePolicyAllocation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_allocations')
    policy = models.ForeignKey(LeavePolicy, on_delete=models.CASCADE, related_name='allocations')
    allocation_year = models.IntegerField()
    allocated_days = models.IntegerField()
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pending_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    carryforward_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'policy', 'allocation_year']
        ordering = ['-allocation_year', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.policy.name} ({self.allocation_year})"

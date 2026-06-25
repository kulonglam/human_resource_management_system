from decimal import Decimal

from django.db import models
from django.utils import timezone

from employees.models import Employee
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import LeaveBalance


LEAVE_TYPE_MAP = {
    'annual': 'annual',
    'sick': 'sick',
    'maternity': 'maternity',
    'paternity': 'paternity',
    'casual': 'annual',
    'bereavement': 'annual',
}


def get_applicable_policies(employee):
    policies = LeavePolicy.objects.filter(is_active=True)
    if employee.department_id:
        return policies.filter(
            models.Q(applicable_to_all=True) | models.Q(departments=employee.department),
        ).distinct()
    return policies.filter(applicable_to_all=True)


def sync_employee_allocations(employee, year=None):
    year = year or timezone.now().year
    policies = get_applicable_policies(employee)

    results = []
    for policy in policies:
        allocation, created = LeavePolicyAllocation.objects.update_or_create(
            employee=employee,
            policy=policy,
            allocation_year=year,
            defaults={
                'allocated_days': policy.days_per_year,
            },
        )
        leave_type = LEAVE_TYPE_MAP.get(policy.leave_type, policy.leave_type)
        if leave_type in dict(LeaveBalance._meta.get_field('leave_type').choices):
            LeaveBalance.objects.update_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                defaults={
                    'total_days': policy.days_per_year + int(allocation.carryforward_days),
                },
            )
        results.append({'policy': policy.name, 'allocation_id': allocation.id, 'created': created})
    return results


def sync_all_employees(year=None):
    year = year or timezone.now().year
    summary = {'employees': 0, 'allocations': 0}
    for employee in Employee.objects.filter(is_active=True):
        rows = sync_employee_allocations(employee, year)
        summary['employees'] += 1
        summary['allocations'] += len(rows)
    return summary


def available_days_from_policy(employee, leave_type, year=None):
    year = year or timezone.now().year
    allocation = LeavePolicyAllocation.objects.filter(
        employee=employee,
        policy__leave_type=leave_type,
        allocation_year=year,
    ).select_related('policy').first()
    if allocation:
        allocated = Decimal(allocation.allocated_days) + allocation.carryforward_days
        used = allocation.used_days + allocation.pending_days
        return float(allocated - used)
    return None

"""Leave duration, accrual, and carry-forward utilities."""

from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from employees.models import Employee
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import LeaveBalance


def get_holiday_dates(start_date, end_date):
    from datetime import date

    from attendance.models import PublicHoliday

    holidays = set(
        PublicHoliday.objects.filter(date__gte=start_date, date__lte=end_date).values_list(
            'date', flat=True,
        ),
    )
    for holiday in PublicHoliday.objects.filter(is_recurring=True):
        for year in range(start_date.year, end_date.year + 1):
            try:
                recurring_date = date(year, holiday.date.month, holiday.date.day)
            except ValueError:
                continue
            if start_date <= recurring_date <= end_date:
                holidays.add(recurring_date)
    return holidays


def is_public_holiday(day):
    from attendance.models import PublicHoliday

    if PublicHoliday.objects.filter(date=day).exists():
        return True
    return PublicHoliday.objects.filter(
        is_recurring=True,
        date__month=day.month,
        date__day=day.day,
    ).exists()


def is_working_day(day, holiday_dates=None):
    if day.weekday() >= 5:
        return False
    if holiday_dates is None:
        return not is_public_holiday(day)
    return day not in holiday_dates


def count_working_days(start_date, end_date, holiday_dates=None):
    if end_date < start_date:
        return 0
    if holiday_dates is None:
        holiday_dates = get_holiday_dates(start_date, end_date)

    total = 0
    current = start_date
    while current <= end_date:
        if is_working_day(current, holiday_dates):
            total += 1
        current += timedelta(days=1)
    return total


def calculate_leave_duration(start_date, end_date, is_half_day=False):
    if is_half_day and start_date == end_date:
        return 0.5 if is_working_day(start_date) else 0.0
    return float(count_working_days(start_date, end_date))


def accrue_monthly_balances(year=None, month=None):
    """Accrue one twelfth of annual policy allocation for active employees."""
    now = timezone.now()
    year = year or now.year
    month = month or now.month

    policies = LeavePolicy.objects.filter(is_active=True, leave_type='annual')
    if not policies.exists():
        return {'employees': 0, 'updated': 0}

    accrual_per_policy = {
        policy.id: round(policy.days_per_year / 12, 2) for policy in policies
    }
    updated = 0

    for employee in Employee.objects.filter(is_active=True):
        applicable = policies.filter(
            models.Q(applicable_to_all=True) | models.Q(departments=employee.department),
        ).distinct()
        increment = sum(accrual_per_policy[p.id] for p in applicable)
        if increment <= 0:
            continue

        balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type='annual',
            year=year,
            defaults={'total_days': 0},
        )
        balance.total_days = float(balance.total_days) + increment
        balance.save(update_fields=['total_days'])
        updated += 1

    return {'year': year, 'month': month, 'employees': updated, 'updated': updated}


def carry_forward_balances(from_year, to_year):
    """Move unused annual leave into the next year subject to policy limits."""
    from leave_policies.services import LEAVE_TYPE_MAP

    carried = 0
    policies = {
        policy.leave_type: policy
        for policy in LeavePolicy.objects.filter(is_active=True, carryforward_allowed=True)
    }

    for allocation in LeavePolicyAllocation.objects.filter(allocation_year=from_year).select_related(
        'employee', 'policy',
    ):
        policy = allocation.policy
        if not policy.carryforward_allowed:
            continue

        leave_type = LEAVE_TYPE_MAP.get(policy.leave_type, policy.leave_type)
        try:
            balance = LeaveBalance.objects.get(
                employee=allocation.employee,
                leave_type=leave_type,
                year=from_year,
            )
        except LeaveBalance.DoesNotExist:
            continue

        unused = Decimal(str(balance.available_days))
        if unused <= 0:
            continue

        limit = policy.carryforward_limit
        carry_amount = float(min(unused, Decimal(limit)) if limit else unused)

        next_balance, _ = LeaveBalance.objects.get_or_create(
            employee=allocation.employee,
            leave_type=leave_type,
            year=to_year,
            defaults={'total_days': 0},
        )
        next_balance.total_days = float(next_balance.total_days) + carry_amount
        next_balance.save(update_fields=['total_days'])

        LeavePolicyAllocation.objects.update_or_create(
            employee=allocation.employee,
            policy=policy,
            allocation_year=to_year,
            defaults={
                'allocated_days': policy.days_per_year,
                'carryforward_days': carry_amount,
            },
        )
        carried += 1

    return {'from_year': from_year, 'to_year': to_year, 'carried': carried}

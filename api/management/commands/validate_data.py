"""Scan the live database for common HR data integrity issues."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q


class Command(BaseCommand):
    help = (
        'Validate live HR data: employees, users, leaves, payroll links, '
        'and other integrity rules. Exits non-zero when errors are found.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Treat warnings as errors (non-zero exit).',
        )

    def handle(self, *args, **options):
        errors: list[str] = []
        warnings: list[str] = []

        self._check_employees(errors, warnings)
        self._check_users(errors, warnings)
        self._check_leaves(errors, warnings)
        self._check_attendance(errors, warnings)
        self._check_payroll(errors, warnings)

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Data validation summary'))
        self.stdout.write(f'  Errors:   {len(errors)}')
        self.stdout.write(f'  Warnings: {len(warnings)}')

        if errors:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('ERRORS'))
            for item in errors:
                self.stdout.write(self.style.ERROR(f'  - {item}'))

        if warnings:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('WARNINGS'))
            for item in warnings:
                self.stdout.write(self.style.WARNING(f'  - {item}'))

        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS('All checks passed.'))
            return

        if errors or (options['strict'] and warnings):
            raise CommandError('Data validation failed.')

        self.stdout.write(self.style.WARNING('Completed with warnings only.'))

    def _check_employees(self, errors, warnings):
        from employees.models import Employee

        today = date.today()
        try:
            min_dob = today.replace(year=today.year - 16)
        except ValueError:
            min_dob = today.replace(year=today.year - 16, day=28)

        total = Employee.objects.count()
        self.stdout.write(f'Employees: {total}')

        blank_ids = list(
            Employee.objects.filter(Q(employee_number__isnull=True) | Q(employee_number=''))
            .values_list('id', 'first_name', 'last_name')[:20]
        )
        for pk, first, last in blank_ids:
            errors.append(f'Employee #{pk} ({first} {last}) has no Employee ID.')

        numbers = list(
            Employee.objects.exclude(employee_number='')
            .values_list('employee_number', flat=True)
        )
        dupes = [num for num, count in Counter(n.upper() for n in numbers).items() if count > 1]
        for num in dupes[:20]:
            errors.append(f'Duplicate Employee ID (case-insensitive): {num}')

        emails = list(Employee.objects.values_list('email', flat=True))
        email_dupes = [
            email for email, count in Counter(e.lower() for e in emails if e).items() if count > 1
        ]
        for email in email_dupes[:20]:
            errors.append(f'Duplicate employee email: {email}')

        for emp in Employee.objects.only(
            'id', 'first_name', 'last_name', 'date_of_birth', 'date_joined',
            'probation_end_date', 'mobile', 'is_active', 'termination_date',
        ).iterator():
            label = f'Employee #{emp.id} ({emp.first_name} {emp.last_name})'
            if emp.date_of_birth and emp.date_of_birth > today:
                errors.append(f'{label}: date of birth is in the future.')
            elif emp.date_of_birth and emp.date_of_birth > min_dob:
                warnings.append(f'{label}: under 16 years old.')
            if emp.date_joined and emp.date_of_birth and emp.date_joined < emp.date_of_birth:
                errors.append(f'{label}: date joined before date of birth.')
            if emp.probation_end_date and emp.date_joined and emp.probation_end_date < emp.date_joined:
                errors.append(f'{label}: probation ends before join date.')
            if emp.mobile:
                digits = re.sub(r'\D', '', emp.mobile)
                if len(digits) < 9 or len(digits) > 15:
                    warnings.append(f'{label}: mobile looks invalid ({emp.mobile}).')
            if emp.termination_date and emp.is_active:
                warnings.append(f'{label}: has termination_date but is still active.')
            if not emp.termination_date and not emp.is_active:
                warnings.append(f'{label}: inactive without termination_date.')

        no_dept = Employee.objects.filter(is_active=True, department__isnull=True).count()
        if no_dept:
            warnings.append(f'{no_dept} active employee(s) have no department.')

    def _check_users(self, errors, warnings):
        from accounts.models import CustomUser, Role
        from employees.models import Employee

        total = CustomUser.objects.count()
        self.stdout.write(f'Users: {total}')

        no_role = CustomUser.objects.filter(role__isnull=True, is_active=True).count()
        if no_role:
            warnings.append(f'{no_role} active user(s) have no role assigned.')

        # Users link to employees by matching email (see UserSerializer).
        employee_emails = {
            email.lower()
            for email in Employee.objects.exclude(email='').values_list('email', flat=True)
            if email
        }

        employee_role = Role.objects.filter(name=Role.EMPLOYEE).first()
        if employee_role:
            unlinked = 0
            for user in CustomUser.objects.filter(
                is_active=True, role=employee_role,
            ).only('id', 'username', 'email'):
                if not user.email or user.email.lower() not in employee_emails:
                    unlinked += 1
            if unlinked:
                warnings.append(
                    f'{unlinked} active employee-role user(s) have no employee record '
                    f'with matching email.',
                )

    def _check_leaves(self, errors, warnings):
        from leaves.models import Leave, LeaveBalance

        total = Leave.objects.count()
        self.stdout.write(f'Leave requests: {total}')

        bad_range = Leave.objects.filter(end_date__lt=F('start_date')).count()
        if bad_range:
            errors.append(f'{bad_range} leave request(s) have end_date before start_date.')

        neg_balance = LeaveBalance.objects.filter(
            Q(total_days__lt=0) | Q(used_days__lt=0) | Q(pending_days__lt=0)
        ).count()
        if neg_balance:
            errors.append(f'{neg_balance} leave balance row(s) have negative values.')

        overused = LeaveBalance.objects.filter(
            used_days__gt=F('total_days') + F('pending_days')
        ).count()
        # used > total is a soft warning (pending may still reconcile)
        over_total = LeaveBalance.objects.filter(used_days__gt=F('total_days')).count()
        if over_total:
            warnings.append(
                f'{over_total} leave balance row(s) have used_days greater than total_days.',
            )
        if overused and overused != over_total:
            warnings.append(
                f'{overused} leave balance row(s) have used_days > total_days + pending_days.',
            )

    def _check_attendance(self, errors, warnings):
        from attendance.models import Attendance

        total = Attendance.objects.count()
        self.stdout.write(f'Attendance rows: {total}')

        # time_out < time_in is valid for overnight / night-shift punches.
        equal = Attendance.objects.exclude(time_in__isnull=True).exclude(
            time_out__isnull=True,
        ).filter(time_in=F('time_out')).count()
        if equal:
            warnings.append(f'{equal} attendance row(s) have identical time_in and time_out.')

    def _check_payroll(self, errors, warnings):
        from payroll.models import Salary

        total = Salary.objects.count()
        self.stdout.write(f'Salary / payslip rows: {total}')

        zero_basic = Salary.objects.filter(basic_salary__lte=0).count()
        if zero_basic:
            warnings.append(f'{zero_basic} salary row(s) have basic_salary ≤ 0.')

        neg_gross = Salary.objects.filter(gross_salary__lt=0).count()
        if neg_gross:
            errors.append(f'{neg_gross} salary row(s) have negative gross_salary.')

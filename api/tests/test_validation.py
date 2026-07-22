"""Tests for strengthened API validation (passwords, leave, employees)."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from leaves.models import Leave, LeaveBalance

from .base import HRAPITestCase


@override_settings(ALLOW_PUBLIC_REGISTRATION=True)
class PasswordValidationTests(HRAPITestCase):
    def test_register_rejects_common_password(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'username': 'newbie',
                'email': 'newbie@test.local',
                'password1': 'password',
                'password2': 'password',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password1', response.data)

    def test_admin_create_user_rejects_short_numeric_password(self):
        self.login('admin', 'AdminPass123!')
        role = self.employee_role
        response = self.client.post(
            '/api/v1/users/',
            {
                'username': 'weakuser',
                'email': 'weak@test.local',
                'first_name': 'Weak',
                'last_name': 'User',
                'role': role.id,
                'password': '12345678',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class LeaveValidationTests(HRAPITestCase):
    def test_rejects_overlapping_leave(self):
        self.login('admin', 'AdminPass123!')
        year = timezone.now().year
        first = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'annual',
                'start_date': f'{year}-07-01',
                'end_date': f'{year}-07-03',
                'reason': 'First',
            },
            format='json',
        )
        self.assertEqual(first.status_code, 201)
        second = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'annual',
                'start_date': f'{year}-07-02',
                'end_date': f'{year}-07-04',
                'reason': 'Overlap',
            },
            format='json',
        )
        self.assertEqual(second.status_code, 400)
        self.assertIn('start_date', second.data)

    def test_rejects_when_no_balance(self):
        self.login('admin', 'AdminPass123!')
        year = timezone.now().year
        response = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'sick',
                'start_date': f'{year}-08-03',
                'end_date': f'{year}-08-03',
                'reason': 'Ill',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('leave_type', response.data)

    def test_rejects_insufficient_balance(self):
        self.login('admin', 'AdminPass123!')
        year = timezone.now().year
        balance = LeaveBalance.objects.get(
            employee=self.employee, leave_type='annual', year=year,
        )
        balance.total_days = 1
        balance.used_days = 0
        balance.pending_days = 0
        balance.save()
        response = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'annual',
                'start_date': f'{year}-07-06',
                'end_date': f'{year}-07-10',
                'reason': 'Too many days',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_unpaid_leave_allowed_without_balance(self):
        self.login('admin', 'AdminPass123!')
        year = timezone.now().year
        response = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'unpaid',
                'start_date': f'{year}-10-05',
                'end_date': f'{year}-10-05',
                'reason': 'Unpaid day',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)


class EmployeeValidationTests(HRAPITestCase):
    def test_rejects_zero_salary(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/employees/',
            {
                'first_name': 'Bad',
                'last_name': 'Salary',
                'date_of_birth': '1990-01-01',
                'gender': 'Male',
                'email': 'badsalary@test.local',
                'mobile': '0700123456',
                'address': 'Kampala',
                'emergency_contact': '0700111222',
                'job_title': 'Clerk',
                'department': self.department.id,
                'date_joined': '2024-01-01',
                'account_number': '111',
                'bank': 'Bank',
                'salary': '0',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('salary', response.data)

    def test_rejects_future_dob(self):
        self.login('admin', 'AdminPass123!')
        future = (date.today() + timedelta(days=5)).isoformat()
        response = self.client.post(
            '/api/v1/employees/',
            {
                'first_name': 'Future',
                'last_name': 'Kid',
                'date_of_birth': future,
                'gender': 'Male',
                'email': 'future@test.local',
                'mobile': '0700123456',
                'address': 'Kampala',
                'emergency_contact': '0700111222',
                'job_title': 'Clerk',
                'department': self.department.id,
                'date_joined': '2024-01-01',
                'account_number': '111',
                'bank': 'Bank',
                'salary': '1000',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('date_of_birth', response.data)

    def test_rejects_digits_in_first_name(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/employees/',
            {
                'first_name': 'John2',
                'last_name': 'Doe',
                'date_of_birth': '1990-01-01',
                'gender': 'Male',
                'email': 'name.digits@test.local',
                'mobile': '0700123456',
                'address': 'Kampala',
                'emergency_contact': '0700111222',
                'job_title': 'Clerk',
                'department': self.department.id,
                'date_joined': '2024-01-01',
                'account_number': '111222',
                'bank': 'Test Bank',
                'salary': '1000',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('first_name', response.data)

    def test_rejects_letters_in_account_number(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/employees/',
            {
                'first_name': 'Jane',
                'last_name': 'Doe',
                'date_of_birth': '1990-01-01',
                'gender': 'Female',
                'email': 'acct.letters@test.local',
                'mobile': '0700123456',
                'address': 'Kampala',
                'emergency_contact': '0700111222',
                'job_title': 'Clerk',
                'department': self.department.id,
                'date_joined': '2024-01-01',
                'account_number': 'ABC123',
                'bank': 'Test Bank',
                'salary': '1000',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('account_number', response.data)

    def test_accepts_alphanumeric_employee_id_and_job_title(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/employees/',
            {
                'employee_number': 'FCA-42',
                'first_name': 'Mary-Jane',
                'last_name': "O'Neil",
                'date_of_birth': '1990-01-01',
                'gender': 'Female',
                'email': 'alpha.ok@test.local',
                'mobile': '+256700123456',
                'address': 'Plot 12, Kampala Rd',
                'emergency_contact': '0700111222',
                'job_title': 'Engineer II',
                'department': self.department.id,
                'date_joined': '2024-01-01',
                'account_number': '1234567890',
                'bank': 'Stanbic Bank',
                'salary': '2500',
                'cost_center': 'CC-100',
                'national_id_number': 'CM123456789ABC',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['employee_number'], 'FCA-42')
        self.assertEqual(response.data['job_title'], 'Engineer II')

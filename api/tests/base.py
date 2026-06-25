from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import CustomUser, Role
from departments.models import Department
from employees.models import Employee
from leaves.models import LeaveBalance


class HRAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(name=Role.ADMIN)
        cls.manager_role = Role.objects.create(name=Role.MANAGER)
        cls.employee_role = Role.objects.create(name=Role.EMPLOYEE)

        cls.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@test.local',
            password='AdminPass123!',
            role=cls.admin_role,
        )
        cls.manager_user = CustomUser.objects.create_user(
            username='manager',
            email='manager@test.local',
            password='ManagerPass123!',
            role=cls.manager_role,
        )
        cls.employee_user = CustomUser.objects.create_user(
            username='employee',
            email='employee@test.local',
            password='EmployeePass123!',
            role=cls.employee_role,
        )

        cls.department = Department.objects.create(name='IT', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='Male',
            email='employee@test.local',
            mobile='0700000000',
            address='Nairobi',
            emergency_contact='0711111111',
            job_title='Developer',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='1234567890',
            bank='Test Bank',
            salary=50000,
        )
        LeaveBalance.objects.create(
            employee=cls.employee,
            leave_type='annual',
            year=timezone.now().year,
            total_days=21,
        )

    def setUp(self):
        self.client = APIClient()

    def login(self, username, password):
        return self.client.post(
            '/api/v1/auth/login/',
            {'username': username, 'password': password},
            format='json',
        )

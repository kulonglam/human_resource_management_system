from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import CustomUser, Role
from accounts.security import clear_failed_logins
from departments.models import Department
from employees.models import Employee
from leaves.models import LeaveBalance

_TEST_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/minute',
        'user': '10000/minute',
        'login': '10000/minute',
        'mfa': '10000/minute',
        'export': '10000/minute',
        'scim': '10000/minute',
    },
}


@override_settings(
    ENFORCE_MFA_FOR_ADMINS=False,
    ENFORCE_MFA_FOR_MANAGERS=False,
    ENFORCE_MFA_FOR_PAYROLL=False,
    REQUIRE_FIELD_ENCRYPTION_KEY=False,
    SESSION_IDLE_TIMEOUT_SECONDS=0,
    REST_FRAMEWORK=_TEST_REST_FRAMEWORK,
)
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
        cache.clear()
        clear_failed_logins('admin')
        clear_failed_logins('manager')
        clear_failed_logins('employee')
        clear_failed_logins('lockout-user')

    def login(self, username, password):
        return self.client.post(
            '/api/v1/auth/login/',
            {'username': username, 'password': password},
            format='json',
        )

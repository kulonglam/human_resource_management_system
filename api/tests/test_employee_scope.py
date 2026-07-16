from employees.models import Employee

from .base import HRAPITestCase


class EmployeeWriteScopeTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_employee = Employee.objects.create(
            first_name='Jane',
            last_name='Other',
            date_of_birth='1992-01-01',
            gender='Female',
            email='other@test.local',
            mobile='0700000001',
            address='Kampala',
            emergency_contact='0711111112',
            job_title='Analyst',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='9876543210',
            bank='Test Bank',
            salary=40000,
        )

    def test_employee_cannot_create_attendance_for_another_employee(self):
        self.login('employee', 'EmployeePass123!')

        response = self.client.post(
            '/api/v1/attendance/',
            {
                'employee': self.other_employee.id,
                'date': '2030-01-02',
                'status': 'present',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_employee_can_create_attendance_for_self(self):
        self.login('employee', 'EmployeePass123!')

        response = self.client.post(
            '/api/v1/attendance/',
            {
                'employee': self.employee.id,
                'date': '2030-01-02',
                'status': 'present',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)

    def test_unlinked_manager_has_no_employee_scope(self):
        self.login('manager', 'ManagerPass123!')

        response = self.client.get('/api/v1/employees/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

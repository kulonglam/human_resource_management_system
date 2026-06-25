from accounts.models import AuditLog

from .base import HRAPITestCase


class EmployeeAPITests(HRAPITestCase):
    def test_admin_lists_employees(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/employees/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_employee_cannot_create_employee(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.post(
            '/api/v1/employees/',
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'date_of_birth': '1992-05-05',
                'gender': 'Female',
                'email': 'jane@test.local',
                'mobile': '0700111222',
                'address': 'Nairobi',
                'emergency_contact': '0700333444',
                'job_title': 'Analyst',
                'department': self.department.id,
                'date_joined': '2025-01-01',
                'account_number': '9876543210',
                'bank': 'Test Bank',
                'salary': 45000,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_create_employee_writes_audit_log(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/employees/',
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'date_of_birth': '1992-05-05',
                'gender': 'Female',
                'email': 'jane@test.local',
                'mobile': '0700111222',
                'address': 'Nairobi',
                'emergency_contact': '0700333444',
                'job_title': 'Analyst',
                'department': self.department.id,
                'date_joined': '2025-01-01',
                'account_number': '9876543210',
                'bank': 'Test Bank',
                'salary': 45000,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(
                action='create',
                model_name='Employee',
                object_id=response.data['id'],
            ).exists()
        )

    def test_admin_can_terminate_employee(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            f'/api/v1/employees/{self.employee.id}/terminate/',
            {'exit_reason': 'resignation', 'exit_notes': 'Voluntary'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_active'])
        self.assertTrue(
            AuditLog.objects.filter(action='update', model_name='Employee', object_id=self.employee.id).exists()
        )

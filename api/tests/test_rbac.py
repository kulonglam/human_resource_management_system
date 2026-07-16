from .base import HRAPITestCase


class RBACTests(HRAPITestCase):
    def test_employee_cannot_view_sensitive_fields(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get(f'/api/v1/employees/{self.employee.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(str(response.data['account_number']).startswith('*'))

    def test_manager_sees_sensitive_fields(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get(f'/api/v1/employees/{self.employee.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['account_number'], '1234567890')

    def test_me_includes_permissions(self):
        self.login('manager', 'ManagerPass123!')
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('permissions', response.data)
        self.assertIn('payroll.view', response.data['permissions'])

    def test_admin_updates_manager_permissions(self):
        from accounts.models import Role

        manager_role = Role.objects.get(name=Role.MANAGER)
        self.login('admin', 'AdminPass123!')
        response = self.client.patch(
            f'/api/v1/roles/{manager_role.id}/',
            {'permissions': ['payroll.view', 'reports.manage']},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['permissions'], ['payroll.view', 'reports.manage'])

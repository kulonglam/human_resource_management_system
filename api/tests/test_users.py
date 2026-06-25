from accounts.models import CustomUser, Role

from .base import HRAPITestCase


class UserManagementTests(HRAPITestCase):
    def test_admin_lists_users(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 200)
        rows = response.data.get('results', response.data)
        self.assertGreaterEqual(len(rows), 3)
        self.assertIn('role_name', rows[0])

    def test_manager_can_list_users(self):
        self.login('manager', 'ManagerPass123!')
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_list_users(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 403)

    def test_admin_creates_user_with_role(self):
        manager_role = Role.objects.get(name=Role.MANAGER)
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/users/',
            {
                'username': 'newmanager',
                'email': 'newmanager@test.local',
                'first_name': 'New',
                'last_name': 'Manager',
                'role': manager_role.id,
                'password': 'SecurePass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['role_name'], Role.MANAGER)
        self.assertTrue(CustomUser.objects.filter(username='newmanager').exists())

    def test_admin_deactivates_user(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.patch(
            f'/api/v1/users/{self.employee_user.id}/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.employee_user.refresh_from_db()
        self.assertFalse(self.employee_user.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.patch(
            f'/api/v1/users/{self.admin_user.id}/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

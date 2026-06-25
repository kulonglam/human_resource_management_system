from django.test import override_settings

from accounts.models import AuditLog, CustomUser

from .base import HRAPITestCase


class AuthTests(HRAPITestCase):
    def test_login_success(self):
        response = self.login('admin', 'AdminPass123!')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'admin')
        self.assertTrue(AuditLog.objects.filter(action='login', user=self.admin_user).exists())

    def test_login_failure(self):
        response = self.login('admin', 'wrong-password')
        self.assertEqual(response.status_code, 400)

    @override_settings(ALLOW_PUBLIC_REGISTRATION=False)
    def test_registration_disabled(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'username': 'newuser',
                'email': 'newuser@test.local',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    def test_registration_forces_employee_role(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'username': 'newhire',
                'email': 'newhire@test.local',
                'role': self.admin_role.id,
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(username='newhire')
        self.assertEqual(user.role.name, 'employee')

    def test_auth_config_endpoint(self):
        response = self.client.get('/api/v1/auth/config/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('allow_registration', response.data)

    def test_roles_require_auth_when_registration_closed(self):
        with override_settings(ALLOW_PUBLIC_REGISTRATION=False):
            response = self.client.get('/api/v1/roles/')
            self.assertIn(response.status_code, (401, 403))

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

    def test_password_reset_request_and_confirm(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.core import mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        response = self.client.post(
            '/api/v1/auth/password-reset/',
            {'email': self.admin_user.email},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reset your password', mail.outbox[0].subject)

        uid = urlsafe_base64_encode(force_bytes(self.admin_user.pk))
        token = default_token_generator.make_token(self.admin_user)
        new_password = 'BrandNewPass123!'
        confirm = self.client.post(
            '/api/v1/auth/password-reset/confirm/',
            {
                'uid': uid,
                'token': token,
                'password': new_password,
                'password_confirm': new_password,
            },
            format='json',
        )
        self.assertEqual(confirm.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password(new_password))

        login = self.client.post(
            '/api/v1/auth/login/',
            {'username': 'admin', 'password': new_password},
            format='json',
        )
        self.assertEqual(login.status_code, 200)

    def test_password_reset_unknown_email_still_ok(self):
        response = self.client.post(
            '/api/v1/auth/password-reset/',
            {'email': 'nobody@example.com'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)

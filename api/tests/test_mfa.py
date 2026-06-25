import pyotp
from django.test import override_settings

from accounts.models import CustomUser

from .base import HRAPITestCase


@override_settings(ENFORCE_MFA_FOR_ADMINS=True)
class MFATests(HRAPITestCase):
    def test_admin_without_mfa_can_login_with_setup_flag(self):
        response = self.login('admin', 'AdminPass123!')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['mfa_setup_required'])
        self.assertFalse(response.data['mfa_enabled'])

    def test_admin_mfa_login_flow(self):
        secret = pyotp.random_base32()
        self.admin_user.mfa_secret = secret
        self.admin_user.mfa_enabled = True
        self.admin_user.save()

        response = self.login('admin', 'AdminPass123!')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['mfa_required'])
        self.assertIn('mfa_token', response.data)

        code = pyotp.TOTP(secret).now()
        verify = self.client.post(
            '/api/v1/auth/mfa/verify/',
            {'mfa_token': response.data['mfa_token'], 'code': code},
            format='json',
        )
        self.assertEqual(verify.status_code, 200)
        self.assertEqual(verify.data['username'], 'admin')

    def test_mfa_setup_requires_admin(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/auth/mfa/setup/')
        self.assertEqual(response.status_code, 403)

    def test_mfa_setup_and_enable(self):
        self.login('admin', 'AdminPass123!')
        setup = self.client.get('/api/v1/auth/mfa/setup/')
        self.assertEqual(setup.status_code, 200)
        secret = setup.data['secret']

        bad = self.client.post('/api/v1/auth/mfa/setup/', {'code': '000000'}, format='json')
        self.assertEqual(bad.status_code, 400)

        code = pyotp.TOTP(secret).now()
        enable = self.client.post('/api/v1/auth/mfa/setup/', {'code': code}, format='json')
        self.assertEqual(enable.status_code, 200)

        user = CustomUser.objects.get(pk=self.admin_user.pk)
        self.assertTrue(user.mfa_enabled)
        self.assertEqual(user.mfa_secret, secret)

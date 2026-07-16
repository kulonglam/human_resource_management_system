from django.core.cache import cache
from django.test import override_settings

from accounts.encryption import decrypt_value, encrypt_value, is_encrypted
from accounts.security import clear_failed_logins, is_login_locked, record_failed_login
from employees.models import Employee

from .base import HRAPITestCase


@override_settings(
    ENFORCE_MFA_FOR_ADMINS=False,
    ENFORCE_MFA_FOR_MANAGERS=False,
    ENFORCE_MFA_FOR_PAYROLL=False,
    LOGIN_LOCKOUT_THRESHOLD=3,
    LOGIN_LOCKOUT_WINDOW_SECONDS=600,
    REQUIRE_FIELD_ENCRYPTION_KEY=False,
)
class SecurityHardeningTests(HRAPITestCase):
    def test_encryption_roundtrip_and_salary_encrypted_at_rest(self):
        encrypted = encrypt_value('50000.00')
        self.assertTrue(is_encrypted(encrypted))
        self.assertEqual(decrypt_value(encrypted), '50000.00')

        employee = Employee.objects.get(pk=self.employee.pk)
        employee.salary = 75000
        employee.bank = 'Stanbic'
        employee.save(update_fields=['salary', 'bank'])
        employee.refresh_from_db()
        self.assertEqual(employee.salary, 75000)
        self.assertEqual(employee.bank, 'Stanbic')

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT salary, bank FROM {Employee._meta.db_table} WHERE id=%s',
                [employee.pk],
            )
            raw_salary, raw_bank = cursor.fetchone()
        self.assertTrue(is_encrypted(raw_salary))
        self.assertTrue(is_encrypted(raw_bank))

    def test_login_lockout_after_failures(self):
        clear_failed_logins('lockout-user')
        for _ in range(3):
            record_failed_login('lockout-user')
        self.assertTrue(is_login_locked('lockout-user'))
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': 'lockout-user', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, 429)
        clear_failed_logins('lockout-user')

    def test_security_headers_present(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Security-Policy', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')

    def test_api_key_scopes_returned_on_create(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/api-keys/',
            {'name': 'scim-key', 'scopes': ['scim', 'read']},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('api_key', response.data)
        self.assertEqual(set(response.data['scopes']), {'scim', 'read'})

    def test_csv_upload_rejects_non_csv(self):
        self.login('manager', 'ManagerPass123!')
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile('notes.exe', b'MZfake', content_type='application/octet-stream')
        response = self.client.post('/api/v1/attendance/import_csv/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 400)

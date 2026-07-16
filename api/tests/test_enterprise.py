import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from accounts.encryption import decrypt_value, encrypt_value, is_encrypted
from accounts.models import SensitiveDataAccessLog
from documents.models import DocumentAccessRule
from employees.models import Employee
from reports.models import ScheduledReport

from .base import HRAPITestCase


class EncryptionTests(HRAPITestCase):
    def test_encrypt_decrypt_roundtrip(self):
        encrypted = encrypt_value('CM12345678')
        self.assertTrue(is_encrypted(encrypted))
        self.assertEqual(decrypt_value(encrypted), 'CM12345678')

    def test_encrypt_employee_pii_command(self):
        Employee.objects.filter(pk=self.employee.pk).update(national_id_number='CF12345678901234')

        from django.core.management import call_command
        call_command('encrypt_employee_pii')

        employee = Employee.objects.get(pk=self.employee.pk)
        self.assertEqual(employee.national_id_number, 'CF12345678901234')


class SensitiveAccessLogTests(HRAPITestCase):
    def test_manager_retrieve_logs_sensitive_access(self):
        self.manager_user.managed_department = self.department
        self.manager_user.save(update_fields=['managed_department'])
        self.login('manager', 'ManagerPass123!')
        before = SensitiveDataAccessLog.objects.count()
        response = self.client.get(f'/api/v1/employees/{self.employee.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SensitiveDataAccessLog.objects.count(), before + 1)

    def test_admin_can_list_sensitive_access_logs(self):
        SensitiveDataAccessLog.objects.create(
            user=self.manager_user,
            employee=self.employee,
            fields_accessed=['account_number'],
        )
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/sensitive-access-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data.get('results', response.data)), 1)


class AttendanceImportTests(HRAPITestCase):
    def test_manager_can_import_attendance_csv(self):
        self.login('manager', 'ManagerPass123!')
        csv_content = (
            'employee_number,date,time_in,time_out,status\n'
            f'{self.employee.employee_number},2026-07-01,08:00,17:00,present\n'
        )
        upload = SimpleUploadedFile('attendance.csv', csv_content.encode('utf-8'), content_type='text/csv')
        response = self.client.post('/api/v1/attendance/import_csv/', {'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['created'], 1)


class ScheduledReportTests(HRAPITestCase):
    @patch('reports.services.EmailMessage.send')
    def test_create_and_run_scheduled_report(self, mock_send):
        self.login('manager', 'ManagerPass123!')
        response = self.client.post(
            '/api/v1/scheduled-reports/',
            {
                'name': 'Weekly attendance',
                'report_type': 'attendance',
                'filters': {'date_range': 'this_month'},
                'frequency': 'weekly',
                'export_format': 'csv',
                'recipient_emails': ['hr@test.local'],
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        scheduled_id = response.data['id']

        run_response = self.client.post(f'/api/v1/scheduled-reports/{scheduled_id}/run_now/', {}, format='json')
        self.assertEqual(run_response.status_code, 200)
        self.assertEqual(run_response.data['status'], 'sent')
        mock_send.assert_called_once()
        self.assertTrue(ScheduledReport.objects.filter(pk=scheduled_id, last_run_at__isnull=False).exists())


class DocumentAccessRuleTests(HRAPITestCase):
    def test_seed_document_access_rules(self):
        from django.core.management import call_command
        call_command('seed_document_access')
        self.assertGreater(DocumentAccessRule.objects.count(), 0)

    def test_employee_cannot_list_contract_documents(self):
        from documents.models import HRDocument
        from django.core.management import call_command

        call_command('seed_document_access')
        HRDocument.objects.create(
            title='Private contract',
            category='contract',
            file='hr_documents/test.pdf',
            employee=self.employee,
        )
        HRDocument.objects.create(
            title='HR Policy',
            category='policy',
            file='hr_documents/policy.pdf',
        )
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, 200)
        categories = {row['category'] for row in response.data.get('results', response.data)}
        self.assertNotIn('contract', categories)
        self.assertIn('policy', categories)


class URAExportTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from payroll.models import Salary

        today = timezone.now().date()
        cls.employee.tax_identification_number = '1000123456'
        cls.employee.save(update_fields=['tax_identification_number'])
        Salary.objects.create(
            employee=cls.employee,
            month=today.month,
            year=today.year,
            basic_salary=1_000_000,
            allowances=100_000,
            deductions=50_000,
            tax=20_000,
            gross_salary=1_100_000,
            chargeable_income=1_050_000,
        )

    def test_ura_paye_export_columns(self):
        self.login('manager', 'ManagerPass123!')
        today = timezone.now().date()
        response = self.client.get(
            f'/api/v1/payroll/statutory-export/?month={today.month}&year={today.year}'
            '&return_type=paye&export_format=ura',
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertIn('TIN', content)
        self.assertIn('Taxpayer Name', content)
        self.assertIn('Tax Deducted', content)

    def test_pdf_report_export(self):
        self.login('manager', 'ManagerPass123!')
        response = self.client.get('/api/v1/reports/attendance/?export_format=pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

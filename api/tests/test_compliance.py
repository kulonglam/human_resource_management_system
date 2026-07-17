from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

from accounts.models import AuditLog
from compliance.models import DataRetentionPolicy
from compliance.retention import apply_all_retention_policies
from employees.models import Employee

from .base import HRAPITestCase


class ComplianceRetentionTests(HRAPITestCase):
    def test_admin_can_list_retention_policies(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/compliance/retention-policies/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 3)

    def test_admin_can_preview_retention(self):
        self.login('admin', 'AdminPass123!')
        AuditLog.objects.create(
            user=self.admin_user,
            action='login',
            model_name='CustomUser',
            timestamp=timezone.now() - timedelta(days=800),
        )
        response = self.client.get('/api/v1/compliance/retention-policies/preview/')
        self.assertEqual(response.status_code, 200)
        audit_preview = next(item for item in response.data if item['category'] == 'audit_logs')
        self.assertGreaterEqual(audit_preview['eligible_count'], 1)

    def test_non_admin_cannot_manage_retention(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/compliance/retention-policies/')
        self.assertEqual(response.status_code, 403)

    def test_apply_retention_purges_old_audit_logs_and_records_run(self):
        policy = DataRetentionPolicy.objects.get(category='audit_logs')
        policy.retention_days = 365
        policy.is_active = True
        policy.save(update_fields=['retention_days', 'is_active'])

        old_log = AuditLog.objects.create(
            user=self.admin_user,
            action='login',
            model_name='CustomUser',
            timestamp=timezone.now() - timedelta(days=400),
        )
        recent_log = AuditLog.objects.create(
            user=self.admin_user,
            action='login',
            model_name='CustomUser',
            timestamp=timezone.now() - timedelta(days=10),
        )

        results = apply_all_retention_policies(dry_run=False)
        audit_result = next(item for item in results if item['category'] == 'audit_logs')
        self.assertGreaterEqual(audit_result['purged'], 1)
        self.assertFalse(AuditLog.objects.filter(pk=old_log.pk).exists())
        self.assertTrue(AuditLog.objects.filter(pk=recent_log.pk).exists())

        policy.refresh_from_db()
        self.assertIsNotNone(policy.last_run_at)
        self.assertGreaterEqual(policy.last_purged_count, 1)

    def test_apply_retention_command_dry_run_does_not_delete(self):
        policy = DataRetentionPolicy.objects.get(category='audit_logs')
        policy.retention_days = 30
        policy.is_active = True
        policy.save(update_fields=['retention_days', 'is_active'])
        AuditLog.objects.create(
            user=self.admin_user,
            action='export',
            model_name='Employee',
            timestamp=timezone.now() - timedelta(days=90),
        )
        before = AuditLog.objects.count()
        call_command('apply_retention_policies', dry_run=True)
        self.assertEqual(AuditLog.objects.count(), before)

    def test_scheduled_tasks_can_skip_retention(self):
        call_command('run_scheduled_tasks', skip_backup=True, skip_retention=True)


class GDPRExportTests(HRAPITestCase):
    def test_employee_can_export_own_data(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/compliance/data-export/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['employee_id'], self.employee.pk)
        self.assertIn('profile', response.data)
        self.assertIn('leave_requests', response.data)

    def test_employee_cannot_export_other_employee(self):
        other = Employee.objects.create(
            first_name='Jane',
            last_name='Smith',
            date_of_birth='1991-02-02',
            gender='Female',
            email='jane@test.local',
            mobile='0700000001',
            address='Nairobi',
            emergency_contact='0711111112',
            job_title='Analyst',
            department=self.department,
            date_joined='2024-02-01',
            account_number='1234567891',
            bank='Test Bank',
            salary=45000,
        )
        self.login('employee', 'EmployeePass123!')
        response = self.client.get(f'/api/v1/compliance/data-export/employees/{other.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_export_employee_data(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get(f'/api/v1/compliance/data-export/employees/{self.employee.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['subject_name'], self.employee.full_name)

    def test_gdpr_erasure_anonymizes_employee(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            f'/api/v1/compliance/erasure/{self.employee.pk}/',
            {'confirm': self.employee.email},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)
        self.assertTrue(self.employee.email.startswith('redacted-'))
        self.employee_user.refresh_from_db()
        self.assertFalse(self.employee_user.is_active)


class AuditLogExportTests(HRAPITestCase):
    def test_admin_can_export_audit_logs_csv(self):
        self.login('admin', 'AdminPass123!')
        AuditLog.objects.create(
            user=self.admin_user,
            action='create',
            model_name='Employee',
            object_id=self.employee.pk,
            object_description='Test',
        )
        response = self.client.get('/api/v1/audit-logs/export/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn(b'Employee', response.content)

    def test_non_admin_cannot_export_audit_logs(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/audit-logs/export/')
        self.assertEqual(response.status_code, 403)

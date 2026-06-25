from accounts.models import AuditLog

from .base import HRAPITestCase


class AuditLogAPITests(HRAPITestCase):
    def test_admin_can_list_audit_logs(self):
        self.login('admin', 'AdminPass123!')
        AuditLog.objects.create(
            user=self.admin_user,
            action='create',
            model_name='Employee',
            object_id=1,
            object_description='Test',
        )
        response = self.client.get('/api/v1/audit-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_non_admin_cannot_list_audit_logs(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/audit-logs/')
        self.assertEqual(response.status_code, 403)

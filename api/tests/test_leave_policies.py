from leave_policies.models import LeavePolicy
from leave_policies.models import LeavePolicyAllocation

from .base import HRAPITestCase


class LeavePolicySyncTests(HRAPITestCase):
    def test_sync_all_employees(self):
        LeavePolicy.objects.create(
            name='Standard Annual',
            leave_type='annual',
            days_per_year=21,
            applicable_to_all=True,
            is_active=True,
        )
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/leave-policy-allocations/sync/',
            {'year': 2026},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['employees'], 1)
        self.assertGreaterEqual(response.data['allocations'], 1)
        self.assertTrue(LeavePolicyAllocation.objects.exists())

    def test_sync_single_employee(self):
        LeavePolicy.objects.create(
            name='Standard Sick',
            leave_type='sick',
            days_per_year=10,
            applicable_to_all=True,
            is_active=True,
        )
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/leave-policy-allocations/sync/',
            {'year': 2026, 'employee': self.employee.id},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['employee'], self.employee.id)
        self.assertGreaterEqual(response.data['synced'], 1)

    def test_employee_cannot_sync_policies(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.post('/api/v1/leave-policy-allocations/sync/', {}, format='json')
        self.assertEqual(response.status_code, 403)

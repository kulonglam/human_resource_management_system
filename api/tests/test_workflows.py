from django.core.management import call_command

from leaves.models import Leave

from .base import HRAPITestCase


class WorkflowTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command('seed_workflows')

    def _create_leave(self):
        self.login('admin', 'AdminPass123!')
        from django.utils import timezone
        year = timezone.now().year
        return self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'annual',
                'start_date': f'{year}-07-01',
                'end_date': f'{year}-07-03',
                'reason': 'Family time',
            },
            format='json',
        )

    def test_leave_creates_approval_request(self):
        response = self._create_leave()
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data.get('approval_status'))
        self.assertEqual(response.data['approval_status']['status'], 'pending')

    def test_list_approval_workflows(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/approval-workflows/')
        self.assertEqual(response.status_code, 200)
        rows = response.data.get('results', response.data)
        self.assertGreaterEqual(len(rows), 1)

    def test_pending_approval_requests_for_admin(self):
        self._create_leave()
        response = self.client.get('/api/v1/approval-requests/')
        self.assertEqual(response.status_code, 200)
        rows = response.data.get('results', response.data)
        self.assertGreaterEqual(len(rows), 1)

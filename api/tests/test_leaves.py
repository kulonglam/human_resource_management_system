from datetime import date
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.utils import timezone

from accounts.models import AuditLog
from leaves.models import Leave

from .base import HRAPITestCase


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LeaveWorkflowTests(HRAPITestCase):
    def _create_leave(self):
        self.login('admin', 'AdminPass123!')
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

    @patch('api.notifications.notify_leave_submitted')
    def test_create_leave_sends_notification(self, mock_notify):
        response = self._create_leave()
        self.assertEqual(response.status_code, 201)
        mock_notify.assert_called_once()
        leave = Leave.objects.get(id=response.data['id'])
        self.assertEqual(leave.status, 'pending')
        self.assertTrue(
            AuditLog.objects.filter(action='create', model_name='Leave', object_id=leave.id).exists()
        )

    @patch('api.viewsets.leaves.notify_leave_decision')
    @patch('api.notifications.notify_leave_submitted')
    def test_approve_leave(self, mock_submitted, mock_notify):
        create_response = self._create_leave()
        leave_id = create_response.data['id']

        response = self.client.post(f'/api/v1/leaves/{leave_id}/approve/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'approved')
        mock_notify.assert_called_once()
        self.assertTrue(
            AuditLog.objects.filter(action='approve', model_name='Leave', object_id=leave_id).exists()
        )

    @patch('api.viewsets.leaves.notify_leave_decision')
    @patch('api.notifications.notify_leave_submitted')
    def test_reject_leave(self, mock_submitted, mock_notify):
        create_response = self._create_leave()
        leave_id = create_response.data['id']

        response = self.client.post(f'/api/v1/leaves/{leave_id}/reject/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'rejected')

    def test_employee_cannot_approve_leave(self):
        create_response = self._create_leave()
        leave_id = create_response.data['id']

        self.client.logout()
        self.login('employee', 'EmployeePass123!')
        response = self.client.post(f'/api/v1/leaves/{leave_id}/approve/', {}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_employee_applies_leave_for_self(self):
        self.login('employee', 'EmployeePass123!')
        year = timezone.now().year
        response = self.client.post(
            '/api/v1/leaves/',
            {
                'leave_type': 'annual',
                'start_date': f'{year}-09-01',
                'end_date': f'{year}-09-02',
                'reason': 'Personal day',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['employee'], self.employee.id)

    def test_employee_cannot_apply_leave_for_other(self):
        from employees.models import Employee

        other = Employee.objects.create(
            first_name='Jane',
            last_name='Other',
            date_of_birth='1992-01-01',
            gender='Female',
            email='other@test.local',
            mobile='0700000001',
            address='Nairobi',
            emergency_contact='0711111112',
            job_title='Analyst',
            department=self.department,
            date_joined='2024-01-01',
            account_number='9876543210',
            bank='Test Bank',
            salary=40000,
        )
        self.login('employee', 'EmployeePass123!')
        year = timezone.now().year
        response = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': other.id,
                'leave_type': 'annual',
                'start_date': f'{year}-09-01',
                'end_date': f'{year}-09-02',
                'reason': 'Invalid',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(HR_NOTIFY_EMAIL='hr@test.local')
    def test_leave_submitted_email(self):
        from api.notifications import notify_leave_submitted

        mail.outbox.clear()
        leave = Leave.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date(timezone.now().year, 8, 1),
            end_date=date(timezone.now().year, 8, 2),
            reason='Test',
        )
        notify_leave_submitted(leave)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('New leave request', mail.outbox[0].subject)

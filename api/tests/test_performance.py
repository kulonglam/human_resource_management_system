from django.core import mail
from django.test import override_settings

from performance.models import PerformanceAppraisal

from .base import HRAPITestCase


def _appraisal_payload(employee):
    return {
        'employee': employee,
        'appraisal_period_start': '2025-01-01',
        'appraisal_period_end': '2025-06-30',
        'job_knowledge': 4,
        'work_quality': 4,
        'productivity': 4,
        'communication': 4,
        'teamwork': 4,
        'initiative': 4,
        'reliability': 4,
        'strengths': 'Strong technical skills',
        'areas_for_improvement': 'Time management',
        'next_goals': 'Lead a project',
    }


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', HR_NOTIFY_EMAIL='hr@test.local')
class PerformanceNotificationTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.appraisal = PerformanceAppraisal.objects.create(**_appraisal_payload(cls.employee))

    def test_appraisal_submit_sends_email(self):
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(
            f'/api/v1/performance-appraisals/{self.appraisal.id}/submit/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'submitted')
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn('Appraisal submitted', mail.outbox[0].subject)

    def test_appraisal_approve_sends_email(self):
        self.appraisal.status = 'submitted'
        self.appraisal.save()
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(
            f'/api/v1/performance-appraisals/{self.appraisal.id}/approve/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'approved')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('approved', mail.outbox[0].subject.lower())

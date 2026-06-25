from django.core import mail
from django.test import override_settings

from recruitment.models import Application, JobPosting

from .base import HRAPITestCase


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RecruitmentNotificationTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.job = JobPosting.objects.create(
            title='Software Engineer',
            department='IT',
            description='Build systems',
            requirements='Python',
            deadline='2025-12-31',
        )
        cls.application = Application.objects.create(
            job=cls.job,
            first_name='Alice',
            last_name='Applicant',
            email='alice@example.com',
            phone='0700123456',
            status='received',
        )

    def test_application_status_change_sends_email(self):
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.patch(
            f'/api/v1/applications/{self.application.id}/',
            {'status': 'shortlisted'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Application update', mail.outbox[0].subject)
        self.assertIn('alice@example.com', mail.outbox[0].to)

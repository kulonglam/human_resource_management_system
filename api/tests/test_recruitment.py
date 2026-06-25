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


class RecruitmentSummaryTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.job = JobPosting.objects.create(
            title='Software Engineer',
            department='IT',
            description='Build systems',
            requirements='Python',
            deadline='2025-12-31',
            is_open=True,
        )
        cls.closed_job = JobPosting.objects.create(
            title='Closed Role',
            department='HR',
            description='Closed',
            requirements='N/A',
            deadline='2025-12-31',
            is_open=False,
        )
        Application.objects.create(
            job=cls.job,
            first_name='Alice',
            last_name='Applicant',
            email='alice@example.com',
            phone='0700123456',
            status='received',
        )
        Application.objects.create(
            job=cls.job,
            first_name='Bob',
            last_name='Shortlist',
            email='bob@example.com',
            phone='0700123457',
            status='shortlisted',
        )

    def test_recruitment_summary_returns_metrics(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/recruitment/summary/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['open_jobs'], 1)
        self.assertEqual(data['total_jobs'], 2)
        self.assertEqual(data['total_applications'], 2)
        self.assertEqual(data['pending_review'], 1)
        self.assertEqual(data['by_status']['received'], 1)
        self.assertEqual(data['by_status']['shortlisted'], 1)
        self.assertEqual(len(data['pipeline']), 2)
        self.assertIn('avg_days_in_pipeline', data)
        self.assertIn('funnel', data)
        self.assertIn('avg_time_to_hire', data)


class PublicCareersTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.job = JobPosting.objects.create(
            title='Public Role',
            department='IT',
            description='Great role',
            requirements='Skills',
            deadline='2099-12-31',
            is_open=True,
        )

    def test_public_job_list(self):
        response = self.client.get('/api/v1/careers/jobs/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Public Role')

    def test_public_apply_creates_application(self):
        response = self.client.post(
            f'/api/v1/careers/jobs/{self.job.id}/apply/',
            {
                'first_name': 'Sam',
                'last_name': 'Candidate',
                'email': 'sam@example.com',
                'phone': '0700999888',
                'cover_letter': 'I am interested.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        app = Application.objects.get(email='sam@example.com')
        self.assertEqual(app.source, 'careers_portal')
        self.assertEqual(app.status, 'received')

from django.core import mail
from django.test import override_settings

from discipline.models import Discipline, DisciplineAppeal

from .base import HRAPITestCase


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', HR_NOTIFY_EMAIL='hr@test.local')
class DisciplineAppealNotificationTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.discipline = Discipline.objects.create(
            employee=cls.employee,
            discipline_type='written_warning',
            reason='Late arrival',
            detailed_reason='Repeated lateness in June',
            incident_date='2025-06-01',
            status='issued',
        )
        cls.appeal = DisciplineAppeal.objects.create(
            discipline=cls.discipline,
            appeal_date='2025-06-10',
            appeal_reason='Medical appointment conflict',
        )

    def test_appeal_create_sends_email(self):
        mail.outbox.clear()
        self.login('admin', 'AdminPass123!')
        discipline = Discipline.objects.create(
            employee=self.employee,
            discipline_type='verbal_warning',
            reason='Policy breach',
            detailed_reason='Details here',
            incident_date='2025-06-15',
            status='issued',
        )
        response = self.client.post(
            '/api/v1/discipline-appeals/',
            {
                'discipline': discipline.id,
                'appeal_date': '2025-06-20',
                'appeal_reason': 'Unfair warning',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('appeal', mail.outbox[0].subject.lower())

    def test_appeal_approve_sends_email(self):
        discipline = Discipline.objects.create(
            employee=self.employee,
            discipline_type='suspension',
            reason='Absence',
            detailed_reason='Unauthorised absence',
            incident_date='2025-06-05',
            status='issued',
        )
        appeal = DisciplineAppeal.objects.create(
            discipline=discipline,
            appeal_date='2025-06-12',
            appeal_reason='Approved leave not recorded',
        )
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(
            f'/api/v1/discipline-appeals/{appeal.id}/approve/',
            {'review_notes': 'Appeal upheld'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'approved')
        self.assertEqual(len(mail.outbox), 1)

    def test_appeal_reject_sends_email(self):
        discipline = Discipline.objects.create(
            employee=self.employee,
            discipline_type='final_warning',
            reason='Conduct',
            detailed_reason='Workplace conduct issue',
            incident_date='2025-06-08',
            status='issued',
        )
        appeal = DisciplineAppeal.objects.create(
            discipline=discipline,
            appeal_date='2025-06-14',
            appeal_reason='Dispute facts',
        )
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(
            f'/api/v1/discipline-appeals/{appeal.id}/reject/',
            {'review_notes': 'Insufficient evidence'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'rejected')
        self.assertEqual(len(mail.outbox), 1)

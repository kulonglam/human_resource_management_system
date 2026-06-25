from django.core import mail
from django.test import override_settings

from benefits.models import Benefit, EmployeeBenefit

from .base import HRAPITestCase


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', HR_NOTIFY_EMAIL='hr@test.local')
class BenefitNotificationTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.benefit = Benefit.objects.create(
            name='Health Cover',
            benefit_type='health',
            description='Medical insurance',
        )

    def test_pending_enrollment_notifies_hr(self):
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(
            '/api/v1/employee-benefits/',
            {
                'employee': self.employee.id,
                'benefit': self.benefit.id,
                'enrollment_date': '2025-06-01',
                'status': 'pending',
                'plan_type': 'Family',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('enrollment', mail.outbox[0].subject.lower())

    def test_activate_enrollment_notifies_employee(self):
        enrollment = EmployeeBenefit.objects.create(
            employee=self.employee,
            benefit=self.benefit,
            enrollment_date='2025-06-01',
            status='pending',
            plan_type='Family',
        )
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.patch(
            f'/api/v1/employee-benefits/{enrollment.id}/',
            {'status': 'active'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('approved', mail.outbox[0].subject.lower())

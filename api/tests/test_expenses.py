from django.core import mail
from django.test import override_settings

from expenses.models import Expense, ExpenseCategory

from .base import HRAPITestCase


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', HR_NOTIFY_EMAIL='hr@test.local')
class ExpenseNotificationTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category = ExpenseCategory.objects.create(name='Travel')

    def test_expense_approve_sends_email(self):
        expense = Expense.objects.create(
            employee=self.employee,
            category=self.category,
            description='Client visit',
            amount='1500.00',
            expense_date='2025-06-01',
            status='submitted',
        )
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(f'/api/v1/expenses/{expense.id}/approve/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('approved', mail.outbox[0].subject.lower())

    def test_expense_reject_sends_email(self):
        expense = Expense.objects.create(
            employee=self.employee,
            category=self.category,
            description='Supplies',
            amount='500.00',
            expense_date='2025-06-02',
            status='submitted',
        )
        self.login('admin', 'AdminPass123!')
        mail.outbox.clear()
        response = self.client.post(
            f'/api/v1/expenses/{expense.id}/reject/',
            {'reason': 'Missing receipt'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('rejected', mail.outbox[0].subject.lower())

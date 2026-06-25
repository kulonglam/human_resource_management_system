from django.core.management import call_command

from integrations.models import WebhookDelivery, WebhookEndpoint

from .base import HRAPITestCase


class WebhookDeliveryTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command('seed_workflows')

    def setUp(self):
        super().setUp()
        self.endpoint = WebhookEndpoint.objects.create(
            name='Test Hook',
            url='https://example.com/hook',
            events=['leave.submitted'],
        )
        WebhookDelivery.objects.create(
            endpoint=self.endpoint,
            event='leave.submitted',
            payload={'event': 'leave.submitted', 'data': {'id': 1}},
            status_code=200,
            success=True,
        )
        WebhookDelivery.objects.create(
            endpoint=self.endpoint,
            event='leave.submitted',
            payload={'event': 'leave.submitted', 'data': {'id': 2}},
            success=False,
            error_message='Connection refused',
        )

    def test_delivery_log(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/webhooks/delivery-log/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertIn('payload', response.data[0])

    def test_delivery_log_filter_success(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/webhooks/delivery-log/?success=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(row['success'] for row in response.data))

    def test_webhook_endpoint_deliveries(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get(f'/api/v1/webhooks/{self.endpoint.id}/deliveries/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_employee_cannot_view_delivery_log(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/webhooks/delivery-log/')
        self.assertEqual(response.status_code, 403)

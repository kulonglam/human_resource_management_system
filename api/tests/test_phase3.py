from integrations.models import APIKey, WebhookEndpoint

from .base import HRAPITestCase


class Phase3IntegrationTests(HRAPITestCase):
    def test_org_chart_endpoint(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/departments/org_chart/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('roots', response.data)

    def test_payroll_export_json(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/payroll/export/?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('rows', response.data)

    def test_sso_config_public(self):
        response = self.client.get('/api/v1/auth/sso/config/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('providers', response.data)

    def test_api_key_create(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post('/api/v1/api-keys/', {'name': 'CI Test Key'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('api_key', response.data)
        self.assertTrue(APIKey.objects.filter(name='CI Test Key').exists())

    def test_webhook_events_list(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/webhooks/events/')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['events']), 0)

    def test_dashboard_role_fields(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['dashboard_role'], 'hr')
        self.assertIn('exec_summary', response.data)

    def test_employee_dashboard_role(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['dashboard_role'], 'employee')

    def test_api_key_authentication(self):
        self.login('admin', 'AdminPass123!')
        create = self.client.post('/api/v1/api-keys/', {'name': 'Auth Test'}, format='json')
        raw_key = create.data['api_key']

        self.client.logout()
        response = self.client.get(
            '/api/v1/health/',
            HTTP_AUTHORIZATION=f'Api-Key {raw_key}',
        )
        self.assertEqual(response.status_code, 200)

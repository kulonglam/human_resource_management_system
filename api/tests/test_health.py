from django.test import override_settings

from .base import HRAPITestCase


class HealthCheckTests(HRAPITestCase):
    def test_health_check_public(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['database'], 'ok')

    def test_health_check_no_auth_required(self):
        response = self.client.get('/api/v1/health/')
        self.assertNotIn(response.status_code, (401, 403))

from django.test import override_settings

from .base import HRAPITestCase


@override_settings(ENFORCE_MFA_FOR_ADMINS=False)
class DashboardTests(HRAPITestCase):
    def test_dashboard_requires_auth(self):
        response = self.client.get('/api/v1/dashboard/')
        self.assertIn(response.status_code, (401, 403))

    def test_dashboard_returns_metrics(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_employees', response.data)
        self.assertIn('pending_leaves', response.data)
        self.assertIn('hero_kpis', response.data)
        self.assertIn('chart', response.data)
        self.assertIn('pending_items', response.data)
        self.assertIn('recent_activity', response.data)
        self.assertIn('attention_items', response.data)
        self.assertIn('exec_analytics', response.data)
        self.assertIn('exec_brief', response.data)

    def test_reports_overview_via_filters(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/reports/filters/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('departments', response.data)
        self.assertIn('overview', response.data)
        self.assertIn('present_today', response.data['overview'])

    def test_reports_analytics_deprecated_alias(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/reports/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('present_today', response.data)
        self.assertEqual(response.get('Deprecation'), 'true')

from io import StringIO

from django.core.cache import cache
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from accounts.models import Notification

from .base import HRAPITestCase


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.local',
    HR_NOTIFY_EMAIL='ops@test.local',
    SLO_ALERT_MIN_REQUESTS=1,
    OPS_ALERT_COOLDOWN_MINUTES=30,
    SENTRY_DSN='',
)
class OpsAlertTests(HRAPITestCase):
    def test_check_ops_alerts_emits_deduplicated_slo_alert(self):
        hour_key = timezone.now().strftime('%Y%m%d%H')
        cache.set(f'slo:requests:{hour_key}', 10, 3600)
        cache.set(f'slo:errors:{hour_key}', 1, 3600)
        cache.set(f'slo:latency_ms:{hour_key}', 9000, 3600)  # 900ms avg > 800ms target

        stdout = StringIO()
        call_command('check_ops_alerts', stdout=stdout)

        self.assertIn('slo_breach', stdout.getvalue())
        slo_notifications = Notification.objects.filter(title='HRMIS SLO breach detected')
        self.assertEqual(slo_notifications.count(), 1)
        slo_mails = [message for message in mail.outbox if 'SLO breach' in message.subject]
        self.assertEqual(len(slo_mails), 1)
        self.assertIn('Availability 90.0%', slo_mails[0].body)

        call_command('check_ops_alerts', stdout=StringIO())
        self.assertEqual(slo_notifications.count(), 1)
        self.assertEqual(
            len([message for message in mail.outbox if 'SLO breach' in message.subject]),
            1,
        )

    def test_ops_status_includes_alert_history_and_cooldown(self):
        from api.ops_monitoring import OPS_ALERT_HISTORY_KEY, emit_ops_alerts

        hour_key = timezone.now().strftime('%Y%m%d%H')
        cache.set(f'slo:requests:{hour_key}', 10, 3600)
        cache.set(f'slo:errors:{hour_key}', 1, 3600)
        cache.set(f'slo:latency_ms:{hour_key}', 9000, 3600)

        result = emit_ops_alerts()
        self.assertIn('slo_breach', result['alerts_emitted'])

        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/ops/status/')
        self.assertEqual(response.status_code, 200)
        alerts = response.data['alerts']
        self.assertGreaterEqual(alerts['breach_count'], 1)
        self.assertTrue(any(item['key'] == 'slo_breach' for item in alerts['active']))
        self.assertTrue(
            any(item['key'] == 'slo_breach' and item['active'] for item in alerts['cooldowns']),
        )
        self.assertTrue(
            any(item['key'] == 'slo_breach' and item['outcome'] == 'emitted' for item in alerts['recent']),
        )
        history = cache.get(OPS_ALERT_HISTORY_KEY) or []
        self.assertTrue(any(item['key'] == 'slo_breach' for item in history))
        from accounts.models import OpsAlertEvent
        self.assertTrue(
            OpsAlertEvent.objects.filter(key='slo_breach', outcome='emitted').exists(),
        )
        self.assertIn('usage', response.data)
        self.assertIn('total_requests', response.data['usage'])

"""Disaster recovery monitoring and drill tests."""

import sqlite3
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from api.dr_monitoring import (
    _save_state,
    collect_dr_alerts,
    get_dr_snapshot,
)
from compliance.models import ComplianceEvidencePack


@override_settings(ENCRYPT_BACKUPS=True, REQUIRE_FIELD_ENCRYPTION_KEY=False)
class DisasterRecoveryTests(TestCase):
    def setUp(self):
        self.backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self._prior = set(self.backup_dir.iterdir())

    def tearDown(self):
        for path in self.backup_dir.iterdir():
            if path not in self._prior:
                if path.is_file():
                    path.unlink(missing_ok=True)

    def test_verify_and_drill_update_dr_snapshot(self):
        call_command('backup_database', stdout=StringIO())
        created = [p for p in self.backup_dir.iterdir() if p not in self._prior]
        self.assertTrue(created)

        call_command('verify_backup', path=str(created[0]), stdout=StringIO())
        call_command('run_restore_drill', path=str(created[0]), record_evidence=True, stdout=StringIO())

        snapshot = get_dr_snapshot()
        self.assertTrue(snapshot['last_verify']['ok'])
        self.assertTrue(snapshot['last_drill']['ok'])
        self.assertTrue(snapshot['verify_current'])
        self.assertTrue(snapshot['drill_current'])
        self.assertTrue(snapshot['ready_for_failover'])
        self.assertTrue(
            ComplianceEvidencePack.objects.filter(
                control='backup_restore',
                title='Monthly restore drill evidence',
            ).exists(),
        )

    @patch('api.dr_monitoring._latest_backup_metadata', return_value=None)
    def test_collect_dr_alerts_flags_missing_backup(self, _mock_latest):
        alerts = collect_dr_alerts()
        keys = {alert['key'] for alert in alerts}
        self.assertIn('dr_no_backup', keys)

    def test_collect_dr_alerts_flags_stale_verify(self):
        stale_at = (timezone.now() - timedelta(days=40)).isoformat()
        _save_state({
            'verify': {
                'ok': True,
                'checked_at': stale_at,
                'backup_name': 'sqlite_old.sqlite3.enc',
            },
        })
        alerts = collect_dr_alerts()
        self.assertTrue(any(alert['key'] == 'dr_verify_stale' for alert in alerts))

    def test_sqlite_drill_restores_readable_database(self):
        db_path = self.backup_dir / 'manual.sqlite3'
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE django_migrations (id INTEGER)')
        conn.execute('CREATE TABLE accounts_customuser (id INTEGER)')
        conn.execute('INSERT INTO django_migrations VALUES (1)')
        conn.execute('INSERT INTO accounts_customuser VALUES (1)')
        conn.commit()
        conn.close()

        out = StringIO()
        call_command('run_restore_drill', path=str(db_path), stdout=out)
        self.assertIn('Restore drill passed', out.getvalue())

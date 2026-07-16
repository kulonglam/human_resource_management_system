"""Tests for streaming backup encryption and verification."""

import base64
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.encryption import encrypt_value
from api.backup_storage import (
    STREAM_HEADER,
    decrypt_file,
    encrypt_file,
    is_stream_encrypted,
    verify_sqlite_backup,
)


@override_settings(ENCRYPT_BACKUPS=True, REQUIRE_FIELD_ENCRYPTION_KEY=False)
class BackupStorageTests(TestCase):
    def test_stream_encrypt_decrypt_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / 'sample.bin'
            payload = b'x' * (300 * 1024) + b'end-marker'
            plain.write_bytes(payload)

            enc = Path(tmp) / 'sample.bin.enc'
            encrypt_file(plain, enc)
            self.assertTrue(is_stream_encrypted(enc))

            out = Path(tmp) / 'restored.bin'
            decrypt_file(enc, out)
            self.assertEqual(out.read_bytes(), payload)

    def test_legacy_encrypted_backup_still_decrypts(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / 'legacy.sqlite3'
            conn = sqlite3.connect(plain)
            conn.execute('CREATE TABLE t (id INTEGER)')
            conn.commit()
            conn.close()

            plain_b64 = base64.b64encode(plain.read_bytes()).decode('ascii')
            enc = Path(tmp) / 'legacy.sqlite3.enc'
            enc.write_text(encrypt_value(plain_b64), encoding='utf-8')

            out = Path(tmp) / 'restored.sqlite3'
            decrypt_file(enc, out)
            self.assertGreater(out.stat().st_size, 0)

    def test_verify_sqlite_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / 'test.sqlite3'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE django_migrations (id INTEGER)')
            conn.execute('CREATE TABLE accounts_customuser (id INTEGER)')
            conn.execute('INSERT INTO django_migrations VALUES (1)')
            conn.execute('INSERT INTO accounts_customuser VALUES (1)')
            conn.commit()
            conn.close()

            report = verify_sqlite_backup(db_path)
            self.assertTrue(report['ok'])
            self.assertEqual(report['integrity_check'], 'ok')
            self.assertGreaterEqual(report['migration_count'], 1)


@override_settings(ENCRYPT_BACKUPS=True, REQUIRE_FIELD_ENCRYPTION_KEY=False)
class BackupCommandTests(TestCase):
    def setUp(self):
        self.backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self._prior = list(self.backup_dir.iterdir())

    def tearDown(self):
        for path in self.backup_dir.iterdir():
            if path not in self._prior:
                path.unlink(missing_ok=True)

    def test_backup_and_verify_commands(self):
        out = StringIO()
        call_command('backup_database', stdout=out)
        output = out.getvalue()
        self.assertIn('Backup', output)

        candidates = sorted(
            [p for p in self.backup_dir.iterdir() if p not in self._prior],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        self.assertTrue(candidates)
        latest = candidates[0]

        verify_out = StringIO()
        call_command('verify_backup', path=str(latest), stdout=verify_out)
        self.assertIn('verification passed', verify_out.getvalue().lower())

    def test_restore_requires_force(self):
        with self.assertRaises(Exception):
            call_command('restore_database', 'nonexistent.sqlite3')

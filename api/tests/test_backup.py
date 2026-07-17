"""Tests for streaming backup encryption and verification."""

import base64
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.encryption import _derive_fernet, encrypt_value
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

    def test_uses_dedicated_backup_key_not_field_key(self):
        payload = b'separate-key-payload'
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / 'sample.bin'
            plain.write_bytes(payload)
            enc = Path(tmp) / 'sample.bin.enc'
            with override_settings(
                BACKUP_ENCRYPTION_KEY='backup-only-secret-key',
                FIELD_ENCRYPTION_KEY='field-only-secret-key',
            ):
                encrypt_file(plain, enc)

            with override_settings(
                BACKUP_ENCRYPTION_KEY='',
                BACKUP_ENCRYPTION_KEY_PREVIOUS='',
                FIELD_ENCRYPTION_KEY='field-only-secret-key',
                FIELD_ENCRYPTION_KEY_PREVIOUS='',
            ):
                out = Path(tmp) / 'fail.bin'
                with self.assertRaises(ValueError):
                    decrypt_file(enc, out)

            with override_settings(
                BACKUP_ENCRYPTION_KEY='backup-only-secret-key',
                FIELD_ENCRYPTION_KEY='field-only-secret-key',
            ):
                out = Path(tmp) / 'ok.bin'
                decrypt_file(enc, out)
                self.assertEqual(out.read_bytes(), payload)

    def test_field_key_legacy_stream_still_decrypts(self):
        """Older stream backups encrypted with FIELD_ENCRYPTION_KEY remain readable."""
        payload = b'legacy-field-encrypted'
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / 'sample.bin'
            plain.write_bytes(payload)
            enc = Path(tmp) / 'sample.bin.enc'
            field_fernet = _derive_fernet('old-field-key')
            with enc.open('w', encoding='utf-8') as dst:
                dst.write(STREAM_HEADER + '\n')
                dst.write(field_fernet.encrypt(payload).decode('ascii') + '\n')

            with override_settings(
                BACKUP_ENCRYPTION_KEY='new-backup-key',
                FIELD_ENCRYPTION_KEY='old-field-key',
            ):
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
            with override_settings(FIELD_ENCRYPTION_KEY='legacy-field-key'):
                enc.write_text(encrypt_value(plain_b64), encoding='utf-8')

            out = Path(tmp) / 'restored.sqlite3'
            with override_settings(
                BACKUP_ENCRYPTION_KEY='unrelated-backup-key',
                FIELD_ENCRYPTION_KEY='legacy-field-key',
            ):
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

    def test_backup_leaves_no_plaintext_when_encrypted(self):
        out = StringIO()
        call_command('backup_database', stdout=out)
        created = [p for p in self.backup_dir.iterdir() if p not in self._prior]
        self.assertTrue(created)
        for path in created:
            self.assertTrue(path.name.endswith('.enc'), path.name)
            self.assertFalse(path.name.endswith('.sqlite3'))
        self.assertIn('no plaintext', out.getvalue().lower())

    def test_secure_delete_removes_file(self):
        from api.backup_storage import secure_delete

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'secret.bin'
            path.write_bytes(b'sensitive-data' * 100)
            secure_delete(path)
            self.assertFalse(path.exists())

    def test_verify_postgres_custom_magic(self):
        from api.backup_storage import verify_postgres_dump

        with tempfile.TemporaryDirectory() as tmp:
            dump = Path(tmp) / 'sample.dump'
            # Minimal custom-format header (PGDMP) + padding
            dump.write_bytes(b'PGDMP' + b'\x00' * 2000)
            report = verify_postgres_dump(dump)
            self.assertTrue(report['ok'])
            self.assertEqual(report['format'], 'custom')

    def test_plain_backup_suffix(self):
        from api.backup_storage import plain_backup_suffix

        self.assertEqual(plain_backup_suffix('sqlite_x.sqlite3.enc'), '.sqlite3')
        self.assertEqual(plain_backup_suffix('postgres_x.dump.enc'), '.dump')
        self.assertEqual(plain_backup_suffix('postgres_x.sql.enc'), '.sql')

    def test_prune_keeps_newest_count(self):
        from api.backup_storage import prune_local_backups
        import os
        import time

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for i in range(5):
                p = root / f'sqlite_2026010{i}_000000.sqlite3.enc'
                p.write_text('x', encoding='utf-8')
                # Stagger mtimes so sort order is deterministic
                os.utime(p, (time.time() - (5 - i) * 100, time.time() - (5 - i) * 100))
                paths.append(p)
            deleted = prune_local_backups(root, keep_count=2, keep_days=0)
            remaining = sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            self.assertEqual(len(remaining), 2)
            self.assertEqual(len(deleted), 3)

    def test_prune_protects_latest(self):
        from api.backup_storage import prune_local_backups
        import os
        import time

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / 'sqlite_old.sqlite3.enc'
            new = root / 'sqlite_new.sqlite3.enc'
            old.write_text('old', encoding='utf-8')
            new.write_text('new', encoding='utf-8')
            os.utime(old, (time.time() - 10_000, time.time() - 10_000))
            deleted = prune_local_backups(root, keep_count=1, keep_days=0, protect=new)
            self.assertTrue(new.exists())
            self.assertFalse(old.exists())
            self.assertEqual(deleted, ['sqlite_old.sqlite3.enc'])

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

    @override_settings(BACKUP_S3_BUCKET='hrmis-test-backups')
    def test_s3_upload_failure_fails_closed(self):
        with patch(
            'api.management.commands.backup_database.upload_backup_to_s3',
            side_effect=RuntimeError('AccessDenied'),
        ):
            with self.assertRaises(CommandError) as ctx:
                call_command('backup_database')
        self.assertIn('failing closed', str(ctx.exception).lower())
        self.assertIn('AccessDenied', str(ctx.exception))

    @override_settings(BACKUP_S3_BUCKET='hrmis-test-backups')
    def test_s3_upload_success_reports_uri(self):
        with patch(
            'api.management.commands.backup_database.upload_backup_to_s3',
            return_value='s3://hrmis-test-backups/hrmis-backups/sqlite_test.enc',
        ):
            out = StringIO()
            call_command('backup_database', stdout=out)
        self.assertIn('Uploaded to s3://hrmis-test-backups/', out.getvalue())

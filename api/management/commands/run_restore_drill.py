"""Run an isolated restore drill without touching the live database."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from api.backup_storage import (
    decrypt_file,
    is_postgres_custom_dump,
    list_backup_files,
    plain_backup_suffix,
    secure_delete,
    verify_postgres_dump,
    verify_sqlite_backup,
)
from api.dr_monitoring import record_dr_event, update_drill_evidence_pack


class Command(BaseCommand):
    help = (
        'Restore the latest backup into an isolated scratch database, measure restore time, '
        'and record DR evidence. Never overwrites the live database.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default='',
            help='Backup file path. Defaults to newest file in backups/.',
        )
        parser.add_argument(
            '--create-if-missing',
            action='store_true',
            help='Run backup_database first when no backup exists.',
        )
        parser.add_argument(
            '--record-evidence',
            action='store_true',
            help='Update compliance evidence pack with drill results.',
        )

    def handle(self, *args, **options):
        started = time.monotonic()
        backup_path = self._resolve_path(options['path'], options['create_if_missing'])
        self.stdout.write(f'Running restore drill for: {backup_path}')

        plain_path = backup_path
        temp_dir = Path(tempfile.mkdtemp(prefix='hrmis_drill_'))
        scratch_db = None
        drill_db_name = None
        try:
            if backup_path.suffix == '.enc':
                plain_path = temp_dir / f'drill{plain_backup_suffix(backup_path.name)}'
                decrypt_file(backup_path, plain_path)
                self.stdout.write(self.style.SUCCESS('Decryption OK'))

            engine = settings.DATABASES['default']['ENGINE']
            if 'sqlite' in engine or plain_path.suffix == '.sqlite3':
                mode = 'sqlite_scratch_restore'
                scratch_db = temp_dir / 'restored.sqlite3'
                shutil.copy2(plain_path, scratch_db)
                report = verify_sqlite_backup(scratch_db)
                if not report.get('ok'):
                    raise CommandError(f'SQLite restore drill failed: {report}')
                details = report
            elif (
                'postgresql' in engine
                or plain_path.suffix in {'.dump', '.sql'}
                or 'postgres' in backup_path.name.lower()
            ):
                details, mode, drill_db_name = self._postgres_drill(plain_path)
            else:
                raise CommandError(f'Unsupported backup type for engine {engine}')

            restore_seconds = round(time.monotonic() - started, 2)
            result = record_dr_event('drill', {
                'ok': True,
                'mode': mode,
                'backup_name': backup_path.name,
                'restore_seconds': restore_seconds,
                'details': details,
            })
            if options['record_evidence']:
                update_drill_evidence_pack(result)

            self.stdout.write(self.style.SUCCESS(
                f'Restore drill passed in {restore_seconds}s ({mode})',
            ))
        except Exception as exc:
            restore_seconds = round(time.monotonic() - started, 2)
            result = record_dr_event('drill', {
                'ok': False,
                'mode': 'failed',
                'backup_name': backup_path.name,
                'restore_seconds': restore_seconds,
                'error': str(exc),
            })
            if options['record_evidence']:
                update_drill_evidence_pack(result)
            raise CommandError(f'Restore drill failed: {exc}') from exc
        finally:
            if scratch_db and scratch_db.exists():
                secure_delete(scratch_db)
            if drill_db_name:
                self._drop_postgres_db(drill_db_name)
            if temp_dir.exists():
                for path in temp_dir.rglob('*'):
                    if path.is_file():
                        secure_delete(path)
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _postgres_drill(self, plain_path: Path):
        db_settings = settings.DATABASES['default']
        report = verify_postgres_dump(plain_path)
        if not report.get('ok'):
            raise CommandError(f'PostgreSQL dump verification failed: {report}')

        drill_db_name = f'hrmis_drill_{uuid.uuid4().hex[:8]}'
        try:
            self._create_postgres_db(drill_db_name, db_settings)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f'Full PostgreSQL restore drill unavailable ({exc}); using verify-only mode.',
            ))
            return report, 'postgres_verify_only', None

        try:
            self._restore_postgres_db(plain_path, drill_db_name, db_settings)
            counts = self._query_postgres_counts(drill_db_name, db_settings)
            return {**report, **counts}, 'postgres_scratch_restore', drill_db_name
        except Exception as exc:
            self._drop_postgres_db(drill_db_name)
            self.stdout.write(self.style.WARNING(
                f'Full PostgreSQL restore drill unavailable ({exc}); using verify-only mode.',
            ))
            return report, 'postgres_verify_only', None

    def _postgres_env(self, db_settings):
        env = os.environ.copy()
        if db_settings.get('PASSWORD'):
            env['PGPASSWORD'] = db_settings['PASSWORD']
        return env

    def _postgres_args(self, db_settings):
        return {
            'host': db_settings.get('HOST', 'localhost'),
            'port': str(db_settings.get('PORT', '5432')),
            'user': db_settings.get('USER', 'postgres'),
        }

    def _create_postgres_db(self, db_name, db_settings):
        args = self._postgres_args(db_settings)
        subprocess.run(
            ['createdb', '-h', args['host'], '-p', args['port'], '-U', args['user'], db_name],
            check=True,
            env=self._postgres_env(db_settings),
            capture_output=True,
        )

    def _drop_postgres_db(self, db_name):
        db_settings = settings.DATABASES['default']
        args = self._postgres_args(db_settings)
        subprocess.run(
            ['dropdb', '--if-exists', '-h', args['host'], '-p', args['port'], '-U', args['user'], db_name],
            env=self._postgres_env(db_settings),
            capture_output=True,
        )

    def _restore_postgres_db(self, plain_path, db_name, db_settings):
        args = self._postgres_args(db_settings)
        env = self._postgres_env(db_settings)
        if is_postgres_custom_dump(plain_path) or plain_path.suffix == '.dump':
            cmd = [
                'pg_restore',
                '-h', args['host'],
                '-p', args['port'],
                '-U', args['user'],
                '-d', db_name,
                '--no-owner',
                '--no-acl',
                str(plain_path),
            ]
            result = subprocess.run(cmd, env=env, capture_output=True)
            if result.returncode > 1:
                err = result.stderr.decode('utf-8', errors='replace')
                raise CommandError(f'pg_restore drill failed: {err}')
            return

        cmd = [
            'psql',
            '-h', args['host'],
            '-p', args['port'],
            '-U', args['user'],
            '-d', db_name,
            '-v', 'ON_ERROR_STOP=1',
            '-f', str(plain_path),
        ]
        subprocess.run(cmd, check=True, env=env, capture_output=True)

    def _query_postgres_counts(self, db_name, db_settings):
        args = self._postgres_args(db_settings)
        env = self._postgres_env(db_settings)
        migrations = self._psql_scalar(
            db_name, 'SELECT COUNT(*) FROM django_migrations;', args, env,
        )
        users = self._psql_scalar(
            db_name, 'SELECT COUNT(*) FROM accounts_customuser;', args, env,
        )
        return {'migration_count': migrations, 'user_count': users}

    def _psql_scalar(self, db_name, sql, args, env):
        result = subprocess.run(
            [
                'psql',
                '-h', args['host'],
                '-p', args['port'],
                '-U', args['user'],
                '-d', db_name,
                '-t', '-A',
                '-c', sql,
            ],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        return int(result.stdout.strip() or 0)

    def _resolve_path(self, path_arg: str, create_if_missing: bool) -> Path:
        if path_arg:
            path = Path(path_arg)
            if not path.exists():
                raise CommandError(f'Backup not found: {path}')
            return path

        files = list_backup_files()
        if not files:
            if create_if_missing:
                call_command('backup_database')
                files = list_backup_files()
            else:
                raise CommandError('No backups found in backups/. Run backup_database or pass --path.')
        return files[0]

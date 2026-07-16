"""Verify latest or specified backup without touching the live database."""

import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from api.backup_storage import (
    decrypt_file,
    is_legacy_encrypted,
    is_stream_encrypted,
    verify_sqlite_backup,
)


class Command(BaseCommand):
    help = 'Verify backup decrypts and passes integrity checks (SQLite) or non-empty SQL dump.'

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

    def handle(self, *args, **options):
        backup_path = self._resolve_path(options['path'], options['create_if_missing'])
        self.stdout.write(f'Verifying backup: {backup_path}')

        engine = settings.DATABASES['default']['ENGINE']
        suffix = '.sqlite3' if 'sqlite' in engine else '.sql'
        work_path = backup_path

        temp_dir = Path(tempfile.mkdtemp(prefix='hrmis_verify_'))
        try:
            if backup_path.suffix == '.enc' or is_stream_encrypted(backup_path) or is_legacy_encrypted(backup_path):
                work_path = temp_dir / f'verify{suffix}'
                decrypt_file(backup_path, work_path)
                self.stdout.write(self.style.SUCCESS('Decryption OK'))

            if 'sqlite' in engine or work_path.suffix == '.sqlite3':
                report = verify_sqlite_backup(work_path)
                self.stdout.write(str(report))
                if not report['ok']:
                    raise CommandError(f'SQLite verification failed: {report}')
                self.stdout.write(self.style.SUCCESS('SQLite backup verification passed'))
                return

            if work_path.suffix == '.sql':
                size = work_path.stat().st_size
                if size < 1024:
                    raise CommandError(f'PostgreSQL dump too small ({size} bytes)')
                head = work_path.read_text(encoding='utf-8', errors='replace')[:500]
                if 'PostgreSQL database dump' not in head and 'CREATE TABLE' not in head:
                    raise CommandError('File does not look like a PostgreSQL dump')
                self.stdout.write(self.style.SUCCESS(f'PostgreSQL dump verification passed ({size} bytes)'))
                return

            raise CommandError(f'Unsupported backup type for engine {engine}')
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _resolve_path(self, path_arg: str, create_if_missing: bool) -> Path:
        if path_arg:
            path = Path(path_arg)
            if not path.exists():
                raise CommandError(f'Backup not found: {path}')
            return path

        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        candidates = sorted(
            [p for p in backup_dir.iterdir() if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            if create_if_missing:
                call_command('backup_database')
                candidates = sorted(
                    [p for p in backup_dir.iterdir() if p.is_file()],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
            else:
                raise CommandError('No backups found in backups/. Run backup_database or pass --path.')
        return candidates[0]

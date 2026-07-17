import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.backup_storage import (
    decrypt_file,
    is_legacy_encrypted,
    is_postgres_custom_dump,
    is_stream_encrypted,
    plain_backup_suffix,
    secure_delete,
)


class Command(BaseCommand):
    help = (
        'Restore a database backup created by backup_database. '
        'PostgreSQL uses pg_restore --clean for custom-format (-Fc) dumps.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            help='Path to .sqlite3, .dump, .sql, or .enc backup file',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Required confirmation to overwrite the live database.',
        )
        parser.add_argument(
            '--no-clean',
            action='store_true',
            help='PostgreSQL only: skip pg_restore --clean/--if-exists (not recommended).',
        )

    def handle(self, *args, **options):
        if not options['force']:
            raise CommandError('Refusing to restore without --force. This overwrites the live database.')

        source = Path(options['path'])
        if not source.exists():
            raise CommandError(f'Backup not found: {source}')

        plain_path = source
        temp_plain = None
        if source.suffix == '.enc' or is_stream_encrypted(source) or is_legacy_encrypted(source):
            suffix = plain_backup_suffix(source.name)
            fd, temp_name = tempfile.mkstemp(prefix='hrmis_restore_', suffix=suffix)
            os.close(fd)
            temp_plain = Path(temp_name)
            plain_path = decrypt_file(source, temp_plain)
            self.stdout.write(self.style.SUCCESS('Decrypted backup to secure temp path'))

        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']

        try:
            if 'sqlite' in engine:
                destination = Path(db_settings['NAME'])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(plain_path, destination)
                self.stdout.write(self.style.SUCCESS('Restored SQLite database'))
                return

            if 'postgresql' in engine:
                self._restore_postgres(plain_path, db_settings, clean=not options['no_clean'])
                return

            raise CommandError(f'Restore not implemented for engine: {engine}')
        finally:
            if temp_plain:
                secure_delete(temp_plain)

    def _restore_postgres(self, plain_path: Path, db_settings: dict, clean: bool) -> None:
        env = os.environ.copy()
        if db_settings.get('PASSWORD'):
            env['PGPASSWORD'] = db_settings['PASSWORD']
        host = db_settings.get('HOST', 'localhost')
        port = str(db_settings.get('PORT', '5432'))
        user = db_settings.get('USER', 'postgres')
        dbname = db_settings['NAME']

        # Custom format (current default) → clean restore via pg_restore
        if is_postgres_custom_dump(plain_path) or plain_path.suffix == '.dump':
            cmd = [
                'pg_restore',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', dbname,
                '--no-owner',
                '--no-acl',
            ]
            if clean:
                cmd.extend(['--clean', '--if-exists'])
            cmd.append(str(plain_path))
            result = subprocess.run(cmd, env=env, capture_output=True)
            # pg_restore may return 1 for non-fatal warnings (e.g. missing roles)
            if result.returncode > 1:
                err = result.stderr.decode('utf-8', errors='replace')
                raise CommandError(f'pg_restore failed (exit {result.returncode}): {err}')
            if result.returncode == 1:
                warn = result.stderr.decode('utf-8', errors='replace').strip()
                if warn:
                    self.stderr.write(self.style.WARNING(f'pg_restore warnings: {warn[:500]}'))
            self.stdout.write(
                self.style.SUCCESS(
                    'Restored PostgreSQL via pg_restore'
                    + (' --clean --if-exists' if clean else '')
                    + ' (custom format)',
                ),
            )
            return

        # Legacy plain SQL dumps
        cmd = [
            'psql',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', dbname,
            '-v', 'ON_ERROR_STOP=1',
            '-f', str(plain_path),
        ]
        subprocess.run(cmd, check=True, env=env)
        self.stdout.write(self.style.SUCCESS('Restored PostgreSQL via psql (legacy plain SQL dump)'))

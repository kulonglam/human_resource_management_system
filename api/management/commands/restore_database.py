import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.backup_storage import decrypt_file, is_legacy_encrypted, is_stream_encrypted


class Command(BaseCommand):
    help = 'Restore a database backup created by backup_database (supports .enc).'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Path to .sqlite3, .sql, or .enc backup file')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Required confirmation to overwrite the live database.',
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
            suffix = '.sqlite3' if 'sqlite' in source.name else '.sql'
            temp_plain = Path(tempfile.gettempdir()) / f'restore_{source.stem}{suffix}'
            plain_path = decrypt_file(source, temp_plain)
            self.stdout.write(self.style.SUCCESS(f'Decrypted backup to {plain_path}'))

        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']

        try:
            if 'sqlite' in engine:
                destination = Path(db_settings['NAME'])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(plain_path, destination)
                self.stdout.write(self.style.SUCCESS(f'Restored SQLite database from {plain_path}'))
                return

            if 'postgresql' in engine:
                env = os.environ.copy()
                if db_settings.get('PASSWORD'):
                    env['PGPASSWORD'] = db_settings['PASSWORD']
                cmd = [
                    'psql',
                    '-h', db_settings.get('HOST', 'localhost'),
                    '-p', str(db_settings.get('PORT', '5432')),
                    '-U', db_settings.get('USER', 'postgres'),
                    '-d', db_settings['NAME'],
                    '-f', str(plain_path),
                ]
                subprocess.run(cmd, check=True, env=env)
                self.stdout.write(self.style.SUCCESS(f'Restored PostgreSQL database from {plain_path}'))
                return

            raise CommandError(f'Restore not implemented for engine: {engine}')
        finally:
            if temp_plain and temp_plain.exists():
                temp_plain.unlink(missing_ok=True)

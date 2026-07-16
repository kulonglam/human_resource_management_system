import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


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

        if source.suffix == '.enc' or source.name.endswith('.enc'):
            source = self._decrypt_backup(source)

        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']

        if 'sqlite' in engine:
            destination = Path(db_settings['NAME'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            self.stdout.write(self.style.SUCCESS(f'Restored SQLite database from {source}'))
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
                '-f', str(source),
            ]
            subprocess.run(cmd, check=True, env=env)
            self.stdout.write(self.style.SUCCESS(f'Restored PostgreSQL database from {source}'))
            return

        raise CommandError(f'Restore not implemented for engine: {engine}')

    def _decrypt_backup(self, enc_path: Path) -> Path:
        import base64

        from accounts.encryption import decrypt_value, is_encrypted

        token = enc_path.read_text(encoding='utf-8').strip()
        if not is_encrypted(token):
            raise CommandError('Encrypted backup does not look like a valid ciphertext.')
        plain_b64 = decrypt_value(token)
        raw = base64.b64decode(plain_b64.encode('ascii'))
        suffix = '.sqlite3' if 'sqlite' in enc_path.name else '.sql'
        tmp = Path(tempfile.gettempdir()) / f'restore_{enc_path.stem}{suffix}'
        tmp.write_bytes(raw)
        self.stdout.write(self.style.SUCCESS(f'Decrypted backup to {tmp}'))
        return tmp

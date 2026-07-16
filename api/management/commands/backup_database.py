import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from api.backup_storage import encrypt_file, upload_backup_to_s3


class Command(BaseCommand):
    help = 'Create a timestamped database backup in the backups/ directory.'

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']

        if 'sqlite' in engine:
            source = Path(db_settings['NAME'])
            destination = backup_dir / f'sqlite_{timestamp}.sqlite3'
            if self._is_memory_sqlite(source):
                self._backup_memory_sqlite(destination)
            else:
                if not source.exists():
                    raise FileNotFoundError(f'SQLite database not found: {source}')
                shutil.copy2(source, destination)
            destination = self._maybe_encrypt(destination)
            self.stdout.write(self.style.SUCCESS(f'Backup saved to {destination}'))
            s3_uri = self._upload_to_s3(destination)
            if s3_uri:
                self.stdout.write(self.style.SUCCESS(f'Uploaded to {s3_uri}'))
            return str(destination)

        if 'postgresql' in engine:
            destination = backup_dir / f'postgres_{timestamp}.sql'
            env = os.environ.copy()
            if db_settings.get('PASSWORD'):
                env['PGPASSWORD'] = db_settings['PASSWORD']
            cmd = [
                'pg_dump',
                '-h', db_settings.get('HOST', 'localhost'),
                '-p', str(db_settings.get('PORT', '5432')),
                '-U', db_settings.get('USER', 'postgres'),
                '-d', db_settings['NAME'],
                '-f', str(destination),
            ]
            subprocess.run(cmd, check=True, env=env)
            destination = self._maybe_encrypt(destination)
            self.stdout.write(self.style.SUCCESS(f'Backup saved to {destination}'))
            s3_uri = self._upload_to_s3(destination)
            if s3_uri:
                self.stdout.write(self.style.SUCCESS(f'Uploaded to {s3_uri}'))
            return str(destination)

        raise NotImplementedError(f'Backup not implemented for engine: {engine}')

    def _is_memory_sqlite(self, source: Path) -> bool:
        name = str(source)
        return ':memory:' in name or 'mode=memory' in name

    def _backup_memory_sqlite(self, destination: Path) -> None:
        import sqlite3

        from django.db import connection

        dest_conn = sqlite3.connect(destination)
        try:
            connection.connection.backup(dest_conn)
        finally:
            dest_conn.close()

    def _maybe_encrypt(self, file_path: Path) -> Path:
        if not getattr(settings, 'ENCRYPT_BACKUPS', False):
            return file_path
        enc_path = Path(str(file_path) + '.enc')
        encrypt_file(file_path, enc_path)
        file_path.unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(f'Backup encrypted (streaming) at {enc_path}'))
        return enc_path

    def _upload_to_s3(self, file_path: Path):
        try:
            return upload_backup_to_s3(file_path)
        except Exception as exc:
            self.stderr.write(self.style.WARNING(f'S3 upload skipped: {exc}'))
            return None

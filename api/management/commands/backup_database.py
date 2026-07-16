import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


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
            if not source.exists():
                raise FileNotFoundError(f'SQLite database not found: {source}')
            destination = backup_dir / f'sqlite_{timestamp}.sqlite3'
            shutil.copy2(source, destination)
            destination = self._maybe_encrypt(destination)
            self.stdout.write(self.style.SUCCESS(f'Backup saved to {destination}'))
            self._upload_to_s3(destination)
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
            self._upload_to_s3(destination)
            return str(destination)

        raise NotImplementedError(f'Backup not implemented for engine: {engine}')

    def _maybe_encrypt(self, file_path: Path) -> Path:
        if not getattr(settings, 'ENCRYPT_BACKUPS', False):
            return file_path
        from accounts.encryption import encrypt_value

        raw = Path(file_path).read_bytes()
        # Chunk large files: store as Fernet of base64 for modest DBs; for large use streaming.
        import base64
        payload = base64.b64encode(raw).decode('ascii')
        token = encrypt_value(payload)
        enc_path = Path(str(file_path) + '.enc')
        enc_path.write_text(token, encoding='utf-8')
        Path(file_path).unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(f'Backup encrypted at {enc_path}'))
        return enc_path

    def _upload_to_s3(self, file_path):
        bucket = getattr(settings, 'BACKUP_S3_BUCKET', '')
        if not bucket:
            return None
        try:
            import boto3

            prefix = getattr(settings, 'BACKUP_S3_PREFIX', 'hrmis-backups/')
            key = f'{prefix}{Path(file_path).name}'
            client = boto3.client(
                's3',
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', None) or os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', ''),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
            )
            client.upload_file(str(file_path), bucket, key)
            self.stdout.write(self.style.SUCCESS(f'Backup uploaded to s3://{bucket}/{key}'))
            return key
        except Exception as exc:
            self.stderr.write(self.style.WARNING(f'S3 upload skipped: {exc}'))
            return None

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.backup_storage import (
    encrypt_file,
    encrypt_stream,
    prune_local_backups,
    secure_delete,
    upload_backup_to_s3,
)


class Command(BaseCommand):
    help = 'Create a timestamped database backup in the backups/ directory.'

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']
        encrypt = getattr(settings, 'ENCRYPT_BACKUPS', False)

        if 'sqlite' in engine:
            destination = self._backup_sqlite(backup_dir, timestamp, encrypt)
            self.stdout.write(self.style.SUCCESS(f'Backup saved to {destination}'))
            self._upload_to_s3(destination)
            self._prune(destination)
            return str(destination)

        if 'postgresql' in engine:
            destination = self._backup_postgres(backup_dir, timestamp, encrypt, db_settings)
            self.stdout.write(self.style.SUCCESS(f'Backup saved to {destination}'))
            self._upload_to_s3(destination)
            self._prune(destination)
            return str(destination)

        raise NotImplementedError(f'Backup not implemented for engine: {engine}')

    def _prune(self, protect: Path) -> None:
        deleted = prune_local_backups(protect=protect)
        if deleted:
            self.stdout.write(self.style.WARNING(f'Pruned {len(deleted)} old backup(s): {", ".join(deleted)}'))

    def _backup_sqlite(self, backup_dir: Path, timestamp: str, encrypt: bool) -> Path:
        """Write SQLite snapshot; when encrypting, only the .enc remains under backups/."""
        source = Path(settings.DATABASES['default']['NAME'])
        if encrypt:
            fd, temp_name = tempfile.mkstemp(prefix='hrmis_bkp_', suffix='.sqlite3')
            os.close(fd)
            temp_path = Path(temp_name)
            enc_path = backup_dir / f'sqlite_{timestamp}.sqlite3.enc'
            try:
                self._write_sqlite_snapshot(source, temp_path)
                encrypt_file(temp_path, enc_path)
                self.stdout.write(self.style.SUCCESS(f'Backup encrypted (no plaintext left) at {enc_path}'))
                return enc_path
            except Exception:
                enc_path.unlink(missing_ok=True)
                raise
            finally:
                secure_delete(temp_path)

        destination = backup_dir / f'sqlite_{timestamp}.sqlite3'
        self._write_sqlite_snapshot(source, destination)
        return destination

    def _write_sqlite_snapshot(self, source: Path, destination: Path) -> None:
        if self._is_memory_sqlite(source):
            self._backup_memory_sqlite(destination)
            return
        if not source.exists():
            raise FileNotFoundError(f'SQLite database not found: {source}')
        # Consistent snapshot via SQLite backup API (avoids copying a mid-write file).
        import sqlite3

        src = sqlite3.connect(f'file:{source}?mode=ro', uri=True)
        dst = sqlite3.connect(destination)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

    def _backup_postgres(self, backup_dir: Path, timestamp: str, encrypt: bool, db_settings: dict) -> Path:
        """pg_dump custom format (-Fc): smaller, faster restore via pg_restore --clean."""
        env = os.environ.copy()
        if db_settings.get('PASSWORD'):
            env['PGPASSWORD'] = db_settings['PASSWORD']
        base_cmd = [
            'pg_dump',
            '-Fc',
            '-h', db_settings.get('HOST', 'localhost'),
            '-p', str(db_settings.get('PORT', '5432')),
            '-U', db_settings.get('USER', 'postgres'),
            '-d', db_settings['NAME'],
        ]

        if encrypt:
            enc_path = backup_dir / f'postgres_{timestamp}.dump.enc'
            proc = subprocess.Popen(
                base_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            try:
                assert proc.stdout is not None
                encrypt_stream(proc.stdout, enc_path)
                stderr = proc.stderr.read() if proc.stderr else b''
                code = proc.wait()
                if code != 0:
                    secure_delete(enc_path)
                    raise CommandError(
                        f'pg_dump failed (exit {code}): {stderr.decode("utf-8", errors="replace")}',
                    )
                self.stdout.write(
                    self.style.SUCCESS(f'Backup encrypted (custom format, no plaintext) at {enc_path}'),
                )
                return enc_path
            except Exception:
                secure_delete(enc_path)
                if proc.poll() is None:
                    proc.kill()
                raise

        destination = backup_dir / f'postgres_{timestamp}.dump'
        subprocess.run([*base_cmd, '-f', str(destination)], check=True, env=env)
        return destination

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

    def _upload_to_s3(self, file_path: Path) -> str | None:
        """Upload when BACKUP_S3_BUCKET is set. Fail closed on upload errors."""
        bucket = getattr(settings, 'BACKUP_S3_BUCKET', '') or ''
        if not bucket.strip():
            return None
        try:
            s3_uri = upload_backup_to_s3(file_path)
        except Exception as exc:
            raise CommandError(
                f'S3 offsite upload failed (BACKUP_S3_BUCKET={bucket!r}). '
                f'Local backup is at {file_path}, but the job is failing closed so '
                f'operators notice the offsite miss. Error: {exc}',
            ) from exc
        if not s3_uri:
            raise CommandError(
                f'S3 offsite upload returned no URI for bucket {bucket!r}. '
                f'Local backup is at {file_path}.',
            )
        self.stdout.write(self.style.SUCCESS(f'Uploaded to {s3_uri}'))
        return s3_uri

"""Streaming backup encryption/decryption (memory-safe for large dumps)."""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

STREAM_HEADER = 'HRMIS_BKP_STREAM_V1'
CHUNK_SIZE = 256 * 1024  # 256 KiB plaintext per Fernet token

logger = logging.getLogger(__name__)
_warned_fallback = False


def _derive_fernet(key_material: str):
    from accounts.encryption import _derive_fernet as derive

    return derive(key_material)


def _append_unique(materials: list[str], value: str | None) -> None:
    if value and value not in materials:
        materials.append(value)


def _split_previous(raw: str) -> list[str]:
    return [part.strip() for part in (raw or '').split(',') if part.strip()]


def _encrypt_key_material() -> str:
    """Primary material for new backups: dedicated backup key, else field key, else SECRET_KEY."""
    global _warned_fallback

    backup = getattr(settings, 'BACKUP_ENCRYPTION_KEY', '') or ''
    if backup:
        return backup

    if getattr(settings, 'REQUIRE_BACKUP_ENCRYPTION_KEY', False):
        raise ImproperlyConfigured(
            'BACKUP_ENCRYPTION_KEY is required when REQUIRE_BACKUP_ENCRYPTION_KEY=True.',
        )

    field = getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or ''
    if field:
        if not _warned_fallback:
            logger.warning(
                'BACKUP_ENCRYPTION_KEY is unset; encrypting backups with FIELD_ENCRYPTION_KEY. '
                'Set a distinct BACKUP_ENCRYPTION_KEY so dump compromise does not share PII crypto.',
            )
            _warned_fallback = True
        return field

    if getattr(settings, 'REQUIRE_FIELD_ENCRYPTION_KEY', False):
        raise ImproperlyConfigured(
            'Set BACKUP_ENCRYPTION_KEY (preferred) or FIELD_ENCRYPTION_KEY to encrypt backups.',
        )
    return settings.SECRET_KEY


def _decrypt_fernets():
    """
    Fernets tried in order for decrypt:
    1) BACKUP_ENCRYPTION_KEY (+ previous)
    2) FIELD_ENCRYPTION_KEY (+ previous) — legacy stream backups
    3) SECRET_KEY — local/dev fallback
    """
    materials: list[str] = []
    _append_unique(materials, getattr(settings, 'BACKUP_ENCRYPTION_KEY', '') or '')
    for part in _split_previous(getattr(settings, 'BACKUP_ENCRYPTION_KEY_PREVIOUS', '') or ''):
        _append_unique(materials, part)
    _append_unique(materials, getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or '')
    for part in _split_previous(getattr(settings, 'FIELD_ENCRYPTION_KEY_PREVIOUS', '') or ''):
        _append_unique(materials, part)
    if not materials:
        materials.append(settings.SECRET_KEY)
    return [_derive_fernet(m) for m in materials]


def _primary_fernet():
    return _derive_fernet(_encrypt_key_material())


def is_stream_encrypted(path: Path) -> bool:
    with path.open('r', encoding='utf-8') as handle:
        first = handle.readline().strip()
    return first == STREAM_HEADER


def is_legacy_encrypted(path: Path) -> bool:
    with path.open('r', encoding='utf-8') as handle:
        first = handle.readline().strip()
    return first.startswith('enc:v1:')


def encrypt_stream(readable, destination: Path) -> Path:
    """Encrypt a binary readable stream into a chunked Fernet text file."""
    fernet = _primary_fernet()
    with destination.open('w', encoding='utf-8') as dst:
        dst.write(STREAM_HEADER + '\n')
        while True:
            chunk = readable.read(CHUNK_SIZE)
            if not chunk:
                break
            token = fernet.encrypt(chunk).decode('ascii')
            dst.write(token + '\n')
    return destination


def encrypt_file(source: Path, destination: Path) -> Path:
    """Encrypt a file using chunked Fernet tokens (streaming)."""
    with source.open('rb') as src:
        return encrypt_stream(src, destination)


def secure_delete(path: Path) -> None:
    """Overwrite file contents then unlink (best-effort; not SSD cryptographic wipe)."""
    path = Path(path)
    if not path.exists() or not path.is_file():
        return
    try:
        size = path.stat().st_size
        with path.open('r+b') as handle:
            # Overwrite in chunks to avoid holding the whole file in RAM.
            remaining = size
            zeros = b'\x00' * min(CHUNK_SIZE, size or CHUNK_SIZE)
            while remaining > 0:
                n = min(len(zeros), remaining)
                handle.write(zeros[:n])
                remaining -= n
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning('secure_delete failed for %s: %s', path, exc)
        path.unlink(missing_ok=True)


def decrypt_file(enc_path: Path, plain_path: Path) -> Path:
    """Decrypt stream or legacy single-blob backup into plain_path."""
    if is_legacy_encrypted(enc_path):
        return _decrypt_legacy(enc_path, plain_path)
    if not is_stream_encrypted(enc_path):
        raise ValueError(f'Not a recognized encrypted backup: {enc_path}')

    fernets = _decrypt_fernets()
    with enc_path.open('r', encoding='utf-8') as src, plain_path.open('wb') as dst:
        header = src.readline()
        if header.strip() != STREAM_HEADER:
            raise ValueError('Invalid stream backup header')
        for line in src:
            token = line.strip()
            if not token:
                continue
            raw = None
            for fernet in fernets:
                try:
                    raw = fernet.decrypt(token.encode('ascii'))
                    break
                except Exception:
                    continue
            if raw is None:
                raise ValueError('Failed to decrypt backup chunk with configured keys')
            dst.write(raw)
    return plain_path


def _decrypt_legacy(enc_path: Path, plain_path: Path) -> Path:
    """Legacy single-token backups used field encrypt_value; also try backup keys."""
    import base64

    from accounts.encryption import decrypt_value, is_encrypted

    token = enc_path.read_text(encoding='utf-8').strip()
    # Prefer field decrypt (original path); if empty and still encrypted-looking, try backup fernets.
    plain_b64 = decrypt_value(token)
    if plain_b64 and not is_encrypted(plain_b64):
        try:
            plain_path.write_bytes(base64.b64decode(plain_b64.encode('ascii')))
            return plain_path
        except Exception:
            pass

    if not is_encrypted(token):
        raise ValueError('Legacy backup is not an enc:v1 token')

    from accounts.encryption import _PREFIX

    raw_token = token[len(_PREFIX):].encode('utf-8')
    for fernet in _decrypt_fernets():
        try:
            plain_b64 = fernet.decrypt(raw_token).decode('utf-8')
            plain_path.write_bytes(base64.b64decode(plain_b64.encode('ascii')))
            return plain_path
        except Exception:
            continue
    raise ValueError('Failed to decrypt legacy backup with configured keys')


def verify_sqlite_backup(sqlite_path: Path) -> dict:
    """Read-only integrity checks on a SQLite backup file."""
    conn = sqlite3.connect(f'file:{sqlite_path}?mode=ro', uri=True)
    try:
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        tables = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'",
        ).fetchone()[0]
        migrations = 0
        try:
            migrations = conn.execute('SELECT COUNT(*) FROM django_migrations').fetchone()[0]
        except sqlite3.Error:
            pass
        users = 0
        try:
            users = conn.execute('SELECT COUNT(*) FROM accounts_customuser').fetchone()[0]
        except sqlite3.Error:
            pass
        return {
            'integrity_check': integrity,
            'table_count': tables,
            'migration_count': migrations,
            'user_count': users,
            'ok': integrity == 'ok' and tables > 0,
        }
    finally:
        conn.close()


PG_CUSTOM_MAGIC = b'PGDMP'


def plain_backup_suffix(source_name: str) -> str:
    """Choose decrypt/temp suffix from backup filename (legacy .sql vs custom .dump)."""
    name = source_name.lower()
    if 'sqlite' in name:
        return '.sqlite3'
    if name.endswith('.sql.enc') or name.endswith('.sql') or '.sql.' in name:
        return '.sql'
    return '.dump'


def is_postgres_custom_dump(path: Path) -> bool:
    with Path(path).open('rb') as handle:
        return handle.read(5) == PG_CUSTOM_MAGIC


def verify_postgres_dump(dump_path: Path) -> dict:
    """
    Sanity-check a PostgreSQL dump without restoring.
    Prefers custom-format (pg_dump -Fc) magic; still accepts legacy plain SQL.
    """
    path = Path(dump_path)
    size = path.stat().st_size
    if size < 1024:
        return {'ok': False, 'bytes': size, 'error': f'dump too small ({size} bytes)'}

    with path.open('rb') as handle:
        magic = handle.read(5)

    if magic == PG_CUSTOM_MAGIC:
        return {'ok': True, 'format': 'custom', 'bytes': size}

    # Legacy plain-text SQL dumps
    head = path.read_text(encoding='utf-8', errors='replace')[:500]
    if 'PostgreSQL database dump' in head or 'CREATE TABLE' in head:
        return {'ok': True, 'format': 'plain', 'bytes': size}

    return {
        'ok': False,
        'bytes': size,
        'error': 'Not a PostgreSQL custom (-Fc) or plain SQL dump',
    }


def list_backup_files(backup_dir: Path | None = None) -> list[Path]:
    """Return backup artifacts (sqlite_/postgres_*) newest first."""
    root = Path(backup_dir or (Path(settings.BASE_DIR) / 'backups'))
    if not root.exists():
        return []
    files = [
        path for path in root.iterdir()
        if path.is_file() and (
            path.name.startswith('sqlite_') or path.name.startswith('postgres_')
        )
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def prune_local_backups(
    backup_dir: Path | None = None,
    *,
    keep_count: int | None = None,
    keep_days: int | None = None,
    protect: Path | None = None,
) -> list[str]:
    """
    Delete old local backups per retention policy.
    - keep_count: retain this many newest files (0 = skip count rule)
    - keep_days: delete files older than this many days (0 = skip age rule)
    - protect: never delete this path (e.g. the backup just created)
    Returns list of deleted file names.
    """
    import time

    root = Path(backup_dir or (Path(settings.BASE_DIR) / 'backups'))
    if keep_count is None:
        keep_count = int(getattr(settings, 'BACKUP_RETENTION_COUNT', 14) or 0)
    if keep_days is None:
        keep_days = int(getattr(settings, 'BACKUP_RETENTION_DAYS', 30) or 0)

    if keep_count <= 0 and keep_days <= 0:
        return []

    files = list_backup_files(root)
    protect_resolved = protect.resolve() if protect else None
    to_delete: set[Path] = set()

    if keep_count > 0 and len(files) > keep_count:
        to_delete.update(files[keep_count:])

    if keep_days > 0:
        cutoff = time.time() - (keep_days * 86400)
        for path in files:
            if path.stat().st_mtime < cutoff:
                to_delete.add(path)

    deleted: list[str] = []
    for path in sorted(to_delete, key=lambda p: p.stat().st_mtime):
        if protect_resolved and path.resolve() == protect_resolved:
            continue
        secure_delete(path)
        deleted.append(path.name)
        logger.info('Pruned local backup %s', path.name)
    return deleted


def upload_backup_to_s3(file_path: Path) -> str | None:
    bucket = getattr(settings, 'BACKUP_S3_BUCKET', '')
    if not bucket:
        return None

    import boto3

    prefix = getattr(settings, 'BACKUP_S3_PREFIX', 'hrmis-backups/')
    key = f'{prefix}{file_path.name}'
    extra = {}
    sse = getattr(settings, 'BACKUP_S3_SSE', 'AES256')
    if sse:
        extra['ServerSideEncryption'] = sse
    kms_key = getattr(settings, 'BACKUP_S3_SSE_KMS_KEY_ID', '')
    if kms_key and sse == 'aws:kms':
        extra['SSEKMSKeyId'] = kms_key

    client = boto3.client(
        's3',
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', None)
        or __import__('os').environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
        aws_access_key_id=__import__('os').environ.get('AWS_ACCESS_KEY_ID', ''),
        aws_secret_access_key=__import__('os').environ.get('AWS_SECRET_ACCESS_KEY', ''),
    )
    client.upload_file(str(file_path), bucket, key, ExtraArgs=extra)
    return f's3://{bucket}/{key}'

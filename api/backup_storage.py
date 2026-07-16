"""Streaming backup encryption/decryption (memory-safe for large dumps)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from django.conf import settings

STREAM_HEADER = 'HRMIS_BKP_STREAM_V1'
CHUNK_SIZE = 256 * 1024  # 256 KiB plaintext per Fernet token


def _primary_fernet():
    from accounts.encryption import _fernets
    return _fernets()[0]


def is_stream_encrypted(path: Path) -> bool:
    with path.open('r', encoding='utf-8') as handle:
        first = handle.readline().strip()
    return first == STREAM_HEADER


def is_legacy_encrypted(path: Path) -> bool:
    with path.open('r', encoding='utf-8') as handle:
        first = handle.readline().strip()
    return first.startswith('enc:v1:')


def encrypt_file(source: Path, destination: Path) -> Path:
    """Encrypt a file using chunked Fernet tokens (streaming)."""
    fernet = _primary_fernet()
    with source.open('rb') as src, destination.open('w', encoding='utf-8') as dst:
        dst.write(STREAM_HEADER + '\n')
        while True:
            chunk = src.read(CHUNK_SIZE)
            if not chunk:
                break
            token = fernet.encrypt(chunk).decode('ascii')
            dst.write(token + '\n')
    return destination


def decrypt_file(enc_path: Path, plain_path: Path) -> Path:
    """Decrypt stream or legacy single-blob backup into plain_path."""
    if is_legacy_encrypted(enc_path):
        return _decrypt_legacy(enc_path, plain_path)
    if not is_stream_encrypted(enc_path):
        raise ValueError(f'Not a recognized encrypted backup: {enc_path}')

    from accounts.encryption import _fernets

    fernets = _fernets()
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
    import base64

    from accounts.encryption import decrypt_value

    token = enc_path.read_text(encoding='utf-8').strip()
    plain_b64 = decrypt_value(token)
    plain_path.write_bytes(base64.b64decode(plain_b64.encode('ascii')))
    return plain_path


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

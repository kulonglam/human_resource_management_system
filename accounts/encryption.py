"""Fernet encryption for sensitive HR fields at rest (supports key rotation)."""

import base64
import hashlib
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

_PREFIX = 'enc:v1:'


def _derive_fernet(key_material: str):
    from cryptography.fernet import Fernet

    digest = hashlib.sha256(key_material.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _primary_key_material():
    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or ''
    if key:
        return key
    if getattr(settings, 'REQUIRE_FIELD_ENCRYPTION_KEY', False):
        raise ImproperlyConfigured(
            'FIELD_ENCRYPTION_KEY is required when DEBUG is False / REQUIRE_FIELD_ENCRYPTION_KEY=True.',
        )
    # Development-only fallback
    return settings.SECRET_KEY


def _fernets():
    """Primary key first, then previous keys for decryption during rotation."""
    materials = [_primary_key_material()]
    previous = getattr(settings, 'FIELD_ENCRYPTION_KEY_PREVIOUS', '') or ''
    for part in previous.split(','):
        part = part.strip()
        if part and part not in materials:
            materials.append(part)
    return [_derive_fernet(m) for m in materials]


def is_encrypted(value):
    return isinstance(value, str) and value.startswith(_PREFIX)


def encrypt_value(value):
    if value is None or value == '':
        return value
    text = str(value)
    if is_encrypted(text):
        return text
    token = _fernets()[0].encrypt(text.encode('utf-8')).decode('utf-8')
    return f'{_PREFIX}{token}'


def decrypt_value(value):
    if value is None or value == '':
        return value
    text = str(value)
    if not is_encrypted(text):
        return text
    token = text[len(_PREFIX):].encode('utf-8')
    for fernet in _fernets():
        try:
            return fernet.decrypt(token).decode('utf-8')
        except Exception:
            continue
    logger.exception('Failed to decrypt sensitive field value with any configured key')
    return ''

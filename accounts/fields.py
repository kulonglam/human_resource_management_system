from decimal import Decimal, InvalidOperation

from django.db import models

from .encryption import decrypt_value, encrypt_value


class EncryptedCharField(models.TextField):
    """Transparent encrypted text storage for PII and banking identifiers."""

    description = 'Encrypted character field'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        return encrypt_value(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'accounts.fields.EncryptedCharField', args, kwargs


class EncryptedDecimalField(models.TextField):
    """Store Decimal values as Fernet ciphertext."""

    description = 'Encrypted decimal field'

    def __init__(self, *args, **kwargs):
        kwargs.pop('max_digits', None)
        kwargs.pop('decimal_places', None)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('null', True)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        plain = decrypt_value(value)
        if plain in (None, ''):
            return None
        try:
            return Decimal(plain)
        except (InvalidOperation, TypeError):
            return None

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        plain = decrypt_value(value) if isinstance(value, str) else value
        if plain in (None, ''):
            return None
        try:
            return Decimal(str(plain))
        except (InvalidOperation, TypeError):
            return None

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        if isinstance(value, Decimal):
            return encrypt_value(format(value, 'f'))
        return encrypt_value(str(value))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'accounts.fields.EncryptedDecimalField', args, kwargs

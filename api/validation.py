"""Shared domain validation helpers for HR API serializers."""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

# Letters (Unicode letters), spaces, hyphen, apostrophe, period — for personal/org names.
_LETTERS_RE = re.compile(r"^[^\W\d_]+(?:[ '\-.][^\W\d_]+)*$", re.UNICODE)
# Digits only (0-9).
_DIGITS_RE = re.compile(r'^\d+$')
# Letters + digits, with common code separators.
_ALPHANUMERIC_RE = re.compile(r'^[A-Za-z0-9]+(?:[ \-_/]+[A-Za-z0-9]+)*$')
_ADDRESS_RE = re.compile(r'^[A-Za-z0-9]+(?:[ \-_/.,#]+[A-Za-z0-9]+)*$')
# Phone: optional +, then 9–15 digits (spaces/dashes/parens stripped first).
_PHONE_RE = re.compile(r'^\+?\d{9,15}$')


def validate_user_password(password: str, *, user=None) -> str:
    """Run Django AUTH_PASSWORD_VALIDATORS; raise DRF ValidationError on failure."""
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return password


def parse_positive_decimal(value, *, field_name='value'):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise serializers.ValidationError({field_name: 'Enter a valid number.'}) from exc
    if amount <= 0:
        raise serializers.ValidationError({field_name: 'Must be greater than zero.'})
    return amount


def validate_letters_only(value, *, field_label='This field'):
    """Accept letters only (spaces, hyphen, apostrophe, period allowed between words)."""
    if value is None or value == '':
        return value
    cleaned = str(value).strip()
    if not cleaned or not _LETTERS_RE.fullmatch(cleaned):
        raise serializers.ValidationError(
            f'{field_label} must contain letters only (spaces and - \' . allowed).',
        )
    return cleaned


def validate_digits_only(value, *, field_label='This field', min_length=None, max_length=None):
    """Accept integer digits only (0–9)."""
    if value is None or value == '':
        return value
    cleaned = str(value).strip()
    if not _DIGITS_RE.fullmatch(cleaned):
        raise serializers.ValidationError(f'{field_label} must contain digits only.')
    if min_length is not None and len(cleaned) < min_length:
        raise serializers.ValidationError(
            f'{field_label} must be at least {min_length} digits.',
        )
    if max_length is not None and len(cleaned) > max_length:
        raise serializers.ValidationError(
            f'{field_label} must be at most {max_length} digits.',
        )
    return cleaned


def validate_alphanumeric(value, *, field_label='This field', allow_punctuation=False):
    """Accept letters and digits (spaces, hyphen, underscore, slash allowed as separators)."""
    if value is None or value == '':
        return value
    cleaned = str(value).strip()
    pattern = _ADDRESS_RE if allow_punctuation else _ALPHANUMERIC_RE
    if not cleaned or not pattern.fullmatch(cleaned):
        raise serializers.ValidationError(
            f'{field_label} must contain letters and/or numbers only '
            f'(spaces and - _ /{", . #" if allow_punctuation else ""} allowed).',
        )
    return cleaned


def validate_employee_dates(attrs, instance=None):
    """DOB, join date, and probation sanity checks."""
    dob = attrs.get('date_of_birth', getattr(instance, 'date_of_birth', None))
    joined = attrs.get('date_joined', getattr(instance, 'date_joined', None))
    probation = attrs.get('probation_end_date', getattr(instance, 'probation_end_date', None))
    today = date.today()
    errors = {}

    if dob:
        if dob > today:
            errors['date_of_birth'] = 'Date of birth cannot be in the future.'
        else:
            # Minimum working age 16
            min_dob = today.replace(year=today.year - 16)
            try:
                too_young = dob > min_dob
            except ValueError:
                # Feb 29 edge cases
                too_young = dob > today - timedelta(days=16 * 365)
            if too_young:
                errors['date_of_birth'] = 'Employee must be at least 16 years old.'

    if joined and joined > today + timedelta(days=30):
        errors['date_joined'] = 'Date joined cannot be more than 30 days in the future.'

    if dob and joined and joined < dob:
        errors['date_joined'] = 'Date joined cannot be before date of birth.'

    if probation and joined and probation < joined:
        errors['probation_end_date'] = 'Probation end date cannot be before date joined.'

    if errors:
        raise serializers.ValidationError(errors)


def validate_mobile_number(value: str) -> str:
    if value is None or value == '':
        return value
    compact = re.sub(r'[\s\-()]', '', str(value).strip())
    if not _PHONE_RE.fullmatch(compact):
        raise serializers.ValidationError(
            'Enter a valid phone number (digits only, 9–15 digits, optional leading +).',
        )
    return compact


def leave_date_ranges_overlap(start_a, end_a, start_b, end_b) -> bool:
    return start_a <= end_b and start_b <= end_a

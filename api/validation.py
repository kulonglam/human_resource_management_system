"""Shared domain validation helpers for HR API serializers."""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


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
    digits = re.sub(r'\D', '', str(value))
    if len(digits) < 9 or len(digits) > 15:
        raise serializers.ValidationError(
            'Enter a valid phone number (9–15 digits, with optional country code).',
        )
    return value


def leave_date_ranges_overlap(start_a, end_a, start_b, end_b) -> bool:
    return start_a <= end_b and start_b <= end_a

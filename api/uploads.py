"""Validate uploaded HR documents and CSV imports."""

import os

from django.conf import settings
from rest_framework.exceptions import ValidationError

ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx', '.xlsx', '.csv'}
ALLOWED_DOCUMENT_CONTENT_TYPES = {
    'application/pdf',
    'image/png',
    'image/jpeg',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'application/csv',
    'application/vnd.ms-excel',
}
ALLOWED_CSV_EXTENSIONS = {'.csv'}


def validate_upload(file_obj, *, kind='document'):
    if not file_obj:
        raise ValidationError({'file': 'File is required.'})

    max_bytes = int(getattr(settings, 'MAX_UPLOAD_BYTES', 10 * 1024 * 1024))
    size = getattr(file_obj, 'size', 0) or 0
    if size > max_bytes:
        raise ValidationError({'file': f'File exceeds maximum size of {max_bytes // (1024 * 1024)}MB.'})

    name = getattr(file_obj, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    allowed_ext = ALLOWED_CSV_EXTENSIONS if kind == 'csv' else ALLOWED_DOCUMENT_EXTENSIONS
    if ext not in allowed_ext:
        raise ValidationError({'file': f'File type {ext or "(none)"} is not allowed.'})

    content_type = getattr(file_obj, 'content_type', '') or ''
    if kind == 'csv':
        if content_type and content_type not in ('text/csv', 'application/csv', 'application/vnd.ms-excel', 'text/plain', ''):
            # Allow empty content_type from some clients
            if content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES and content_type != 'text/plain':
                raise ValidationError({'file': f'Content type {content_type} is not allowed for CSV.'})
    elif content_type and content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
        raise ValidationError({'file': f'Content type {content_type} is not allowed.'})

    return file_obj

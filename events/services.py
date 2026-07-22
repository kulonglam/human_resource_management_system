"""Domain event outbox publish / drain helpers."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from events.models import DomainEvent

logger = logging.getLogger(__name__)


def publish_event(topic: str, payload: dict | None = None) -> DomainEvent:
    """Enqueue a domain event in the same DB transaction as the caller when possible."""
    return DomainEvent.objects.create(topic=topic, payload=payload or {})


def drain_outbox(*, limit: int = 100, handler=None) -> dict:
    """
    Process pending outbox rows.

    Default handler logs + marks processed. Pass a callable(event) to fan-out
    (webhooks, queues, etc.). Raising marks the row failed.
    """
    processed = 0
    failed = 0
    qs = DomainEvent.objects.filter(status=DomainEvent.STATUS_PENDING).order_by('created_at')[:limit]
    for event in qs:
        with transaction.atomic():
            locked = DomainEvent.objects.select_for_update().filter(
                pk=event.pk, status=DomainEvent.STATUS_PENDING,
            ).first()
            if not locked:
                continue
            locked.attempts += 1
            try:
                if handler:
                    handler(locked)
                else:
                    logger.info('Outbox event processed: %s %s', locked.topic, locked.pk)
                locked.status = DomainEvent.STATUS_PROCESSED
                locked.processed_at = timezone.now()
                locked.error_message = ''
                locked.save(update_fields=['status', 'processed_at', 'error_message', 'attempts'])
                processed += 1
            except Exception as exc:
                locked.status = DomainEvent.STATUS_FAILED
                locked.error_message = str(exc)[:2000]
                locked.save(update_fields=['status', 'error_message', 'attempts'])
                failed += 1
                logger.exception('Outbox event failed: %s', locked.pk)
    return {'processed': processed, 'failed': failed}

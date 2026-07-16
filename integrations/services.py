import hashlib
import hmac
import json
import logging
import uuid

import requests
from django.conf import settings
from django.core.cache import cache

from .models import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)


def _sign_payload(secret, payload_bytes):
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


def dispatch_webhook(event, payload, idempotency_key=None):
    if not getattr(settings, 'WEBHOOKS_ENABLED', True):
        return []

    if idempotency_key:
        cache_key = f'webhook_idem:{idempotency_key}'
        if cache.get(cache_key):
            return []
        cache.set(cache_key, True, 60 * 60 * 24)

    endpoints = WebhookEndpoint.objects.filter(is_active=True)
    results = []
    for endpoint in endpoints:
        if endpoint.events and event not in endpoint.events:
            continue
        results.append(_deliver(endpoint, event, payload, attempt=1, idempotency_key=idempotency_key))
    return results


def _deliver(endpoint, event, data_payload, attempt=1, idempotency_key=None):
    delivery = WebhookDelivery.objects.create(
        endpoint=endpoint,
        event=event,
        payload={},
        attempt_count=attempt,
    )
    body = {
        'event': event,
        'data': data_payload if not isinstance(data_payload, dict) or 'event' not in data_payload else data_payload.get('data', data_payload),
        'delivery_id': delivery.id,
        'idempotency_key': idempotency_key or str(uuid.uuid4()),
    }
    # If caller passed a previously stored payload dict with event/data, normalize
    if isinstance(data_payload, dict) and 'event' in data_payload and 'data' in data_payload:
        body['data'] = data_payload['data']
        if data_payload.get('idempotency_key'):
            body['idempotency_key'] = data_payload['idempotency_key']

    payload_bytes = json.dumps(body, default=str, sort_keys=True).encode()
    headers = {
        'Content-Type': 'application/json',
        'X-HRMIS-Event': event,
        'X-HRMIS-Delivery-Attempt': str(attempt),
        'X-HRMIS-Delivery-Id': str(delivery.id),
        'X-HRMIS-Idempotency-Key': body['idempotency_key'],
    }
    if endpoint.secret:
        headers['X-HRMIS-Signature'] = _sign_payload(endpoint.secret, payload_bytes)
        headers['X-HRMIS-Signature-Alg'] = 'sha256'

    delivery.payload = body
    try:
        response = requests.post(endpoint.url, data=payload_bytes, headers=headers, timeout=10)
        delivery.status_code = response.status_code
        delivery.success = 200 <= response.status_code < 300
        if not delivery.success:
            delivery.error_message = response.text[:500]
    except Exception as exc:
        delivery.success = False
        delivery.error_message = str(exc)[:500]
        logger.exception('Webhook delivery failed: %s', endpoint.url)

    delivery.save(update_fields=['payload', 'status_code', 'success', 'error_message'])
    return delivery


def retry_webhook_delivery(delivery_id):
    delivery = WebhookDelivery.objects.select_related('endpoint').get(pk=delivery_id)
    body = delivery.payload if isinstance(delivery.payload, dict) else {'event': delivery.event, 'data': delivery.payload}
    data = body.get('data', body)
    return _deliver(
        delivery.endpoint,
        delivery.event,
        {'event': delivery.event, 'data': data, 'idempotency_key': body.get('idempotency_key')},
        attempt=delivery.attempt_count + 1,
        idempotency_key=body.get('idempotency_key'),
    )

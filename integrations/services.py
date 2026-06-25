import hashlib
import hmac
import json
import logging

import requests
from django.conf import settings

from .models import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)


def _sign_payload(secret, payload_bytes):
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


def dispatch_webhook(event, payload):
    if not getattr(settings, 'WEBHOOKS_ENABLED', True):
        return []

    endpoints = WebhookEndpoint.objects.filter(is_active=True)
    results = []
    body = {
        'event': event,
        'data': payload,
    }
    payload_bytes = json.dumps(body, default=str).encode()

    for endpoint in endpoints:
        if endpoint.events and event not in endpoint.events:
            continue
        headers = {
            'Content-Type': 'application/json',
            'X-HRMIS-Event': event,
        }
        if endpoint.secret:
            headers['X-HRMIS-Signature'] = _sign_payload(endpoint.secret, payload_bytes)

        delivery = WebhookDelivery(endpoint=endpoint, event=event, payload=body)
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

        delivery.save()
        results.append(delivery)
    return results

"""Shared health/SLO evaluation and alert helpers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import connection
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from api.dr_monitoring import collect_dr_alerts
from api.in_app_notifications import get_hr_users, notify_users
from api.redis_config import infrastructure_snapshot, ping_cache

logger = logging.getLogger(__name__)

OPS_ALERT_HISTORY_KEY = 'ops_alert:history'
OPS_ALERT_HISTORY_LIMIT = 40
KNOWN_ALERT_KEYS = (
    'health_degraded',
    'slo_breach',
    'dr_no_backup',
    'dr_rpo_breach',
    'dr_verify_stale',
    'dr_drill_stale',
    'dr_rto_breach',
)


def get_usage_snapshot(*, now=None):
    """Daily request totals and top API path buckets for cost/ops visibility."""
    now = now or timezone.now()
    day_key = now.strftime('%Y%m%d')
    total = int(cache.get(f'usage:requests:{day_key}') or 0)
    paths = cache.get(f'usage:paths:{day_key}') or []
    if not isinstance(paths, list):
        paths = []
    top = []
    for path in paths:
        count = int(cache.get(f'usage:path:{day_key}:{path}') or 0)
        if count:
            top.append({'path': path, 'requests': count})
    top.sort(key=lambda item: item['requests'], reverse=True)
    return {
        'window': 'current_day',
        'day': day_key,
        'total_requests': total,
        'top_paths': top[:15],
        'checked_at': now.isoformat(),
        'note': 'Coarse path counters for capacity/cost planning; not billable metering.',
    }


def get_health_snapshot():
    db_ok = True
    error = ''
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as exc:
        db_ok = False
        error = str(exc)

    redis_url = getattr(settings, 'REDIS_URL', '')
    if redis_url:
        redis_ok, redis_error = ping_cache()
        redis_status = 'ok' if redis_ok else 'unavailable'
        if not redis_ok:
            error = error or redis_error
    else:
        redis_ok = True
        redis_status = 'not_configured'

    status = 'ok' if db_ok and redis_ok else 'degraded'
    return {
        'status': status,
        'database': 'ok' if db_ok else 'unavailable',
        'redis': redis_status,
        'version': '1.2.0',
        'api_version': 'v1',
        'checked_at': timezone.now().isoformat(),
        'error': error,
        'infrastructure': infrastructure_snapshot(redis_url or None),
    }


def get_slo_snapshot(*, now=None):
    now = now or timezone.now()
    hour_key = now.strftime('%Y%m%d%H')
    requests_count = int(cache.get(f'slo:requests:{hour_key}') or 0)
    errors_count = int(cache.get(f'slo:errors:{hour_key}') or 0)
    latency_sum = float(cache.get(f'slo:latency_ms:{hour_key}') or 0)
    availability = 100.0 if requests_count == 0 else round(
        100.0 * (1 - (errors_count / max(requests_count, 1))), 3,
    )
    avg_latency = 0.0 if requests_count == 0 else round(latency_sum / requests_count, 2)
    targets = {
        'availability_percent': float(getattr(settings, 'SLO_TARGET_AVAILABILITY_PERCENT', 99.5)),
        'error_budget_percent': float(getattr(settings, 'SLO_TARGET_ERROR_BUDGET_PERCENT', 0.5)),
        'avg_latency_ms': float(getattr(settings, 'SLO_TARGET_AVG_LATENCY_MS', 800)),
        'min_requests_for_alert': int(getattr(settings, 'SLO_ALERT_MIN_REQUESTS', 25)),
    }
    within_slo = (
        availability >= targets['availability_percent']
        and avg_latency <= targets['avg_latency_ms']
    )
    return {
        'window': 'current_hour',
        'requests': requests_count,
        'server_errors': errors_count,
        'availability_percent': availability,
        'avg_latency_ms': avg_latency,
        'targets': targets,
        'within_slo': within_slo,
        'request_id_header': 'X-Request-ID',
        'checked_at': now.isoformat(),
    }


def _capture_sentry_alert(level, message, extra):
    if not getattr(settings, 'SENTRY_DSN', ''):
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        logger.exception('Failed to emit Sentry ops alert: %s', message)


def _notify_alert(subject, message, *, category='system', link='/settings/ops'):
    admin_users = list(get_hr_users())
    notify_users(admin_users, subject, message, category, link)
    recipient = getattr(settings, 'HR_NOTIFY_EMAIL', '')
    if recipient:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception('Failed to send ops alert email: %s', subject)
    return len(admin_users)


def _cooldown_minutes():
    return int(getattr(settings, 'OPS_ALERT_COOLDOWN_MINUTES', 30))


def _alert_cache_key(alert_key):
    return f'ops_alert:{alert_key}'


def evaluate_active_alerts(*, health=None, slo=None):
    """Return currently breached alert conditions (independent of cooldown)."""
    health = health or get_health_snapshot()
    slo = slo or get_slo_snapshot()
    alerts = []

    if health['status'] != 'ok':
        alerts.append({
            'key': 'health_degraded',
            'level': 'error',
            'title': 'HRMIS health check degraded',
            'message': (
                f"Database/redis check failed. Status={health['status']} "
                f"database={health['database']} redis={health['redis']}."
            ),
        })

    slo_request_floor = slo['targets']['min_requests_for_alert']
    if slo['requests'] >= slo_request_floor and not slo['within_slo']:
        alerts.append({
            'key': 'slo_breach',
            'level': 'warning',
            'title': 'HRMIS SLO breach detected',
            'message': (
                f"Availability {slo['availability_percent']}% and average latency "
                f"{slo['avg_latency_ms']}ms breached targets "
                f"{slo['targets']['availability_percent']}% / {slo['targets']['avg_latency_ms']}ms."
            ),
        })

    for dr_alert in collect_dr_alerts():
        alerts.append({
            'key': dr_alert['key'],
            'level': dr_alert['level'],
            'title': dr_alert['title'],
            'message': dr_alert['message'],
        })

    return alerts


def _parse_emitted_at(raw):
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if timezone.is_aware(raw) else timezone.make_aware(raw)
    parsed = parse_datetime(str(raw))
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def get_cooldown_status(alert_key, *, now=None, cooldown_minutes=None):
    now = now or timezone.now()
    cooldown_minutes = cooldown_minutes if cooldown_minutes is not None else _cooldown_minutes()
    raw = cache.get(_alert_cache_key(alert_key))
    emitted_at = _parse_emitted_at(raw)
    if not emitted_at:
        return {
            'key': alert_key,
            'active': False,
            'last_emitted_at': None,
            'expires_at': None,
            'remaining_seconds': 0,
        }
    expires_at = emitted_at + timedelta(minutes=cooldown_minutes)
    remaining = max(0, int((expires_at - now).total_seconds()))
    return {
        'key': alert_key,
        'active': remaining > 0,
        'last_emitted_at': emitted_at.isoformat(),
        'expires_at': expires_at.isoformat() if remaining > 0 else None,
        'remaining_seconds': remaining,
    }


def _append_alert_history(entry):
    """Persist alert history to DB; keep a short cache mirror for fast reads."""
    from accounts.models import OpsAlertEvent

    OpsAlertEvent.objects.create(
        key=entry.get('key', ''),
        level=entry.get('level', 'warning'),
        title=entry.get('title', '')[:200],
        message=entry.get('message', ''),
        outcome=entry.get('outcome', 'emitted'),
        payload=entry.get('payload') or {},
        emitted_at=_parse_emitted_at(entry.get('at')) or timezone.now(),
    )
    history = list(cache.get(OPS_ALERT_HISTORY_KEY) or [])
    history.insert(0, entry)
    cache.set(OPS_ALERT_HISTORY_KEY, history[:OPS_ALERT_HISTORY_LIMIT], 60 * 60 * 24 * 14)


def _load_recent_alert_history(limit=OPS_ALERT_HISTORY_LIMIT):
    from accounts.models import OpsAlertEvent

    rows = OpsAlertEvent.objects.order_by('-emitted_at')[:limit]
    return [
        {
            'key': row.key,
            'title': row.title,
            'message': row.message,
            'level': row.level,
            'outcome': row.outcome,
            'at': row.emitted_at.isoformat(),
            'payload': row.payload or {},
        }
        for row in rows
    ]


def prune_ops_alert_history(*, keep_days=90):
    from accounts.models import OpsAlertEvent

    cutoff = timezone.now() - timedelta(days=keep_days)
    deleted, _ = OpsAlertEvent.objects.filter(emitted_at__lt=cutoff).delete()
    return deleted


def get_ops_alerts_snapshot(*, now=None):
    """Active breaches, cooldown state, and recent emit/suppress history for Ops UI."""
    now = now or timezone.now()
    cooldown_minutes = _cooldown_minutes()
    health = get_health_snapshot()
    slo = get_slo_snapshot(now=now)
    active = evaluate_active_alerts(health=health, slo=slo)
    active_keys = {item['key'] for item in active}

    cooldowns = []
    keys = list(dict.fromkeys([*KNOWN_ALERT_KEYS, *active_keys]))
    for key in keys:
        status = get_cooldown_status(key, now=now, cooldown_minutes=cooldown_minutes)
        status['breaching'] = key in active_keys
        if status['active'] or status['breaching']:
            cooldowns.append(status)

    history = _load_recent_alert_history()
    return {
        'cooldown_minutes': cooldown_minutes,
        'checked_at': now.isoformat(),
        'active': active,
        'cooldowns': cooldowns,
        'recent': history[:OPS_ALERT_HISTORY_LIMIT],
        'breach_count': len(active),
        'cooldown_active_count': sum(1 for item in cooldowns if item['active']),
    }


def emit_ops_alerts():
    health = get_health_snapshot()
    slo = get_slo_snapshot()
    cooldown_minutes = _cooldown_minutes()
    alerts = evaluate_active_alerts(health=health, slo=slo)
    detail_by_key = {
        'health_degraded': {'health': health},
        'slo_breach': {'slo': slo},
    }
    for dr_alert in collect_dr_alerts():
        detail_by_key[dr_alert['key']] = dr_alert.get('details') or {}

    emitted = []
    suppressed = []
    now = timezone.now()
    for alert in alerts:
        cache_key = _alert_cache_key(alert['key'])
        if cache.get(cache_key):
            suppressed.append(alert['key'])
            continue
        cache.set(cache_key, now.isoformat(), cooldown_minutes * 60)
        _notify_alert(alert['title'], alert['message'])
        _capture_sentry_alert(
            alert['level'],
            alert['title'],
            detail_by_key.get(alert['key'], {}),
        )
        _append_alert_history({
            'key': alert['key'],
            'title': alert['title'],
            'message': alert['message'],
            'level': alert['level'],
            'outcome': 'emitted',
            'at': now.isoformat(),
        })
        emitted.append(alert['key'])

    return {
        'health': health,
        'slo': slo,
        'alerts_emitted': emitted,
        'alerts_suppressed': suppressed,
    }

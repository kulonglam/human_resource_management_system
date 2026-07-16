"""Login lockout and security event helpers."""

import logging

from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('hrmis.security')


def _fail_key(username: str) -> str:
    return f'login_fail:{(username or "").strip().lower()}'


def is_login_locked(username: str) -> bool:
    threshold = int(getattr(settings, 'LOGIN_LOCKOUT_THRESHOLD', 5))
    return int(cache.get(_fail_key(username)) or 0) >= threshold


def record_failed_login(username: str):
    key = _fail_key(username)
    window = int(getattr(settings, 'LOGIN_LOCKOUT_WINDOW_SECONDS', 900))
    count = int(cache.get(key) or 0) + 1
    cache.set(key, count, window)
    logger.warning('Failed login for %s (count=%s)', username, count)
    return count


def clear_failed_logins(username: str):
    cache.delete(_fail_key(username))


def log_security_event(event: str, detail: str = '', user=None, request=None):
    username = getattr(user, 'username', None) or 'anonymous'
    ip = ''
    if request is not None:
        ip = request.META.get('REMOTE_ADDR', '')
    logger.warning('security_event=%s user=%s ip=%s detail=%s', event, username, ip, detail)

"""Redis URL parsing and Django cache / django-q cluster configuration."""

from __future__ import annotations

from urllib.parse import urlparse


def parse_redis_url(redis_url: str) -> dict:
    """Parse redis:// or rediss:// URLs into django-q redis settings."""
    parsed = urlparse(redis_url)
    if parsed.scheme not in {'redis', 'rediss'}:
        raise ValueError(f'Unsupported Redis URL scheme: {parsed.scheme}')

    db_path = (parsed.path or '').lstrip('/')
    options = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 6379,
        'db': int(db_path) if db_path else 0,
    }
    if parsed.password:
        options['password'] = parsed.password
    if parsed.username:
        options['username'] = parsed.username
    if parsed.scheme == 'rediss':
        options['ssl'] = True
    return options


def build_cache_config(redis_url: str | None) -> dict:
    if redis_url:
        return {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': redis_url,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': 'hrmis',
            },
        }
    return {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'hrmis-local',
        },
    }


def build_q_cluster_config(redis_url: str | None, *, workers: int) -> dict:
    """Return django-q cluster settings using Redis when available, else ORM fallback."""
    base = {
        'name': 'hrmis',
        'workers': workers,
        'timeout': 300,
        'retry': 360,
        'queue_limit': 50,
        'bulk': 10,
        'catch_up': True,
    }
    if redis_url:
        base['redis'] = parse_redis_url(redis_url)
        return base
    base['orm'] = 'default'
    return base


def ping_cache() -> tuple[bool, str]:
    """Lightweight cache connectivity probe used by health checks."""
    try:
        from django.core.cache import cache

        cache.set('health:redis_ping', 'ok', 5)
        if cache.get('health:redis_ping') == 'ok':
            return True, 'ok'
        return False, 'cache read/write mismatch'
    except Exception as exc:
        return False, str(exc)


def infrastructure_snapshot(redis_url: str | None) -> dict:
    return {
        'cache_backend': 'redis' if redis_url else 'locmem',
        'queue_backend': 'redis' if redis_url else 'orm',
        'redis_configured': bool(redis_url),
    }

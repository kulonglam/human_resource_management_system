import secrets

import pyotp
from django.core.cache import cache

PENDING_PREFIX = 'mfa_pending:'
SETUP_PREFIX = 'mfa_setup:'
TOKEN_TTL = 300
SETUP_TTL = 600


def generate_mfa_secret():
    return pyotp.random_base32()


def get_totp(secret):
    return pyotp.TOTP(secret)


def verify_totp(secret, code):
    if not secret or not code:
        return False
    return get_totp(secret).verify(str(code).strip(), valid_window=1)


def create_pending_mfa_token(user_id):
    token = secrets.token_urlsafe(32)
    cache.set(f'{PENDING_PREFIX}{token}', user_id, timeout=TOKEN_TTL)
    return token


def consume_pending_mfa_token(token):
    if not token:
        return None
    key = f'{PENDING_PREFIX}{token}'
    user_id = cache.get(key)
    if user_id is not None:
        cache.delete(key)
    return user_id


def store_setup_secret(user_id, secret):
    cache.set(f'{SETUP_PREFIX}{user_id}', secret, timeout=SETUP_TTL)


def get_setup_secret(user_id):
    return cache.get(f'{SETUP_PREFIX}{user_id}')


def consume_setup_secret(user_id):
    key = f'{SETUP_PREFIX}{user_id}'
    secret = cache.get(key)
    if secret:
        cache.delete(key)
    return secret

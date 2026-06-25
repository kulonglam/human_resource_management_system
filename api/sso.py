import hashlib
import logging
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

SSO_STATE_TTL = 600
STATE_PREFIX = 'sso_state:'


def _callback_base():
    return settings.SSO_CALLBACK_BASE_URL.rstrip('/')


def _provider_config(provider):
    if provider == 'google' and settings.GOOGLE_OAUTH_CLIENT_ID:
        return {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://openidconnect.googleapis.com/v1/userinfo',
            'scope': 'openid email profile',
        }
    if provider == 'microsoft' and settings.MICROSOFT_OAUTH_CLIENT_ID:
        tenant = settings.MICROSOFT_OAUTH_TENANT
        base = f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0'
        return {
            'client_id': settings.MICROSOFT_OAUTH_CLIENT_ID,
            'client_secret': settings.MICROSOFT_OAUTH_CLIENT_SECRET,
            'auth_url': f'{base}/authorize',
            'token_url': f'{base}/token',
            'userinfo_url': 'https://graph.microsoft.com/oidc/userinfo',
            'scope': 'openid email profile',
        }
    return None


def get_enabled_providers():
    providers = []
    if settings.GOOGLE_OAUTH_CLIENT_ID:
        providers.append({'id': 'google', 'name': 'Google'})
    if settings.MICROSOFT_OAUTH_CLIENT_ID:
        providers.append({'id': 'microsoft', 'name': 'Microsoft'})
    return providers


def build_authorization_url(provider):
    config = _provider_config(provider)
    if not config:
        return None, None

    state = secrets.token_urlsafe(32)
    cache.set(f'{STATE_PREFIX}{state}', provider, timeout=SSO_STATE_TTL)

    redirect_uri = f'{_callback_base()}/api/v1/auth/sso/{provider}/callback/'
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'scope': config['scope'],
        'redirect_uri': redirect_uri,
        'state': state,
    }
    if provider == 'google':
        params['access_type'] = 'online'
        params['prompt'] = 'select_account'
    return f"{config['auth_url']}?{urlencode(params)}", state


def consume_state(state):
    key = f'{STATE_PREFIX}{state}'
    provider = cache.get(key)
    if provider:
        cache.delete(key)
    return provider


def exchange_code(provider, code):
    config = _provider_config(provider)
    if not config:
        raise ValueError('SSO provider not configured.')

    redirect_uri = f'{_callback_base()}/api/v1/auth/sso/{provider}/callback/'
    response = requests.post(
        config['token_url'],
        data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        },
        timeout=15,
    )
    response.raise_for_status()
    access_token = response.json()['access_token']

    userinfo = requests.get(
        config['userinfo_url'],
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=15,
    )
    userinfo.raise_for_status()
    data = userinfo.json()
    email = data.get('email') or data.get('preferred_username') or data.get('upn')
    if not email:
        raise ValueError('Email not returned by identity provider.')
    return {
        'email': email.lower(),
        'first_name': data.get('given_name', '')[:150],
        'last_name': data.get('family_name', '')[:150],
        'subject': data.get('sub', ''),
    }

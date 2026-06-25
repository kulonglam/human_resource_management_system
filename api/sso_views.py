import logging

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.utils.text import slugify
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import CustomUser, Role

from .audit import log_action
from .mfa import create_pending_mfa_token
from .serializers import UserSerializer
from .sso import build_authorization_url, consume_state, exchange_code, get_enabled_providers

logger = logging.getLogger(__name__)


def _resolve_sso_user(profile):
    user = CustomUser.objects.filter(email__iexact=profile['email']).first()
    if user:
        return user
    if not settings.SSO_AUTO_PROVISION:
        raise ValueError('No HRMIS account exists for this email. Contact your HR administrator.')

    employee_role = Role.objects.get(name=Role.EMPLOYEE)
    base_username = slugify(profile['email'].split('@')[0]).replace('-', '_') or 'user'
    username = base_username
    suffix = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f'{base_username}{suffix}'
        suffix += 1

    user = CustomUser.objects.create_user(
        username=username,
        email=profile['email'],
        first_name=profile['first_name'] or username,
        last_name=profile['last_name'],
        role=employee_role,
    )
    user.set_unusable_password()
    user.save()
    return user


class SSOConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'providers': get_enabled_providers()})


class SSOStartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, provider):
        auth_url, state = build_authorization_url(provider)
        if not auth_url:
            return Response({'detail': 'SSO provider not configured.'}, status=404)
        return Response({'authorization_url': auth_url, 'state': state})


class SSOCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, provider):
        error = request.query_params.get('error')
        if error:
            return HttpResponseRedirect(f'{settings.SSO_FRONTEND_REDIRECT}?sso_error={error}')

        code = request.query_params.get('code')
        state = request.query_params.get('state')
        if not code or not state or consume_state(state) != provider:
            return HttpResponseRedirect(f'{settings.SSO_FRONTEND_REDIRECT}?sso_error=invalid_state')

        try:
            profile = exchange_code(provider, code)
            user = _resolve_sso_user(profile)
        except Exception as exc:
            logger.exception('SSO callback failed')
            return HttpResponseRedirect(
                f'{settings.SSO_FRONTEND_REDIRECT}?sso_error={str(exc).replace(" ", "_")[:80]}'
            )

        if not user.is_active:
            return HttpResponseRedirect(f'{settings.SSO_FRONTEND_REDIRECT}?sso_error=account_disabled')

        if settings.ENFORCE_MFA_FOR_ADMINS and user.is_admin and user.mfa_enabled and user.mfa_secret:
            token = create_pending_mfa_token(user.id)
            return HttpResponseRedirect(
                f'{settings.SSO_FRONTEND_REDIRECT}?mfa_required=1&mfa_token={token}'
            )

        login(request, user)
        log_action(request, 'login', 'CustomUser', user.id, user.username, f'SSO login ({provider})')

        if settings.ENFORCE_MFA_FOR_ADMINS and user.is_admin and not user.mfa_enabled:
            return HttpResponseRedirect(f'{settings.SSO_FRONTEND_REDIRECT}?mfa_setup_required=1')

        return HttpResponseRedirect(settings.SSO_FRONTEND_REDIRECT)

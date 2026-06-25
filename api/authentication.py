from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from integrations.models import APIKey


class APIKeyAuthentication(BaseAuthentication):
    keyword = 'Api-Key'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith(f'{self.keyword} '):
            return None

        raw_key = auth_header[len(self.keyword) + 1:].strip()
        user = APIKey.authenticate(raw_key)
        if not user:
            raise AuthenticationFailed('Invalid API key.')
        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')
        return user, None

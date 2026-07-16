from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from integrations.models import APIKey


class APIKeyAuthentication(BaseAuthentication):
    keyword = 'Api-Key'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        # Support Api-Key and Bearer (for SCIM IdPs)
        raw_key = None
        if auth_header.startswith(f'{self.keyword} '):
            raw_key = auth_header[len(self.keyword) + 1:].strip()
        elif auth_header.startswith('Bearer '):
            raw_key = auth_header[7:].strip()

        if not raw_key:
            return None

        api_key = APIKey.authenticate(raw_key)
        if not api_key:
            raise AuthenticationFailed('Invalid API key.')
        user = api_key.user
        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')
        request.auth_api_key = api_key
        return user, api_key

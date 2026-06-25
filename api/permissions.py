from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS


class RequiresMFASetupComplete(BasePermission):
    """Block admin API access until TOTP MFA is enabled (mirrors SPA guard)."""

    MFA_SETUP_PATHS = (
        '/api/v1/auth/logout/',
        '/api/v1/auth/me/',
        '/api/v1/auth/mfa/setup/',
        '/api/v1/auth/mfa/verify/',
        '/api/v1/auth/csrf/',
    )

    message = 'Complete MFA setup at /settings/security before using the API.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return True
        if not getattr(settings, 'ENFORCE_MFA_FOR_ADMINS', True):
            return True
        user = request.user
        if not getattr(user, 'is_admin', False) or user.mfa_enabled:
            return True
        path = request.path
        return any(path.startswith(p) or path == p.rstrip('/') for p in self.MFA_SETUP_PATHS)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'is_admin', False)


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (
            getattr(user, 'is_admin', False) or getattr(user, 'is_manager', False)
        )


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and getattr(request.user, 'is_admin', False)


class IsAdminOrManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return IsAdminOrManager().has_permission(request, view)

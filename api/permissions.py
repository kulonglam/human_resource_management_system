from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.access_control import (
    can_access_payroll,
    can_approve_attendance,
    can_manage_payroll,
    can_manage_reports,
    can_view_sensitive_data,
    user_has_permission,
)
from accounts.models import Role


def _mfa_setup_allowed(path):
    paths = (
        '/api/v1/auth/logout/',
        '/api/v1/auth/me/',
        '/api/v1/auth/mfa/setup/',
        '/api/v1/auth/mfa/verify/',
        '/api/v1/auth/csrf/',
    )
    return any(path.startswith(p) or path == p.rstrip('/') for p in paths)


def _user_requires_mfa_setup(user):
    if user.mfa_enabled:
        return False
    if getattr(user, 'is_admin', False) and getattr(settings, 'ENFORCE_MFA_FOR_ADMINS', True):
        return True
    if getattr(user, 'is_manager', False) and getattr(settings, 'ENFORCE_MFA_FOR_MANAGERS', False):
        return True
    return False


class RequiresMFASetupComplete(BasePermission):
    """Block privileged API access until TOTP MFA is enabled (mirrors SPA guard)."""

    message = 'Complete MFA setup at /settings/security before using the API.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return True
        if not _user_requires_mfa_setup(request.user):
            return True
        return _mfa_setup_allowed(request.path)


class RequiresMFAForPayroll(BasePermission):
    """Step-up control: payroll users must have MFA enabled when enforcement is on."""

    message = 'Enable MFA before accessing payroll data.'

    def has_permission(self, request, view):
        if not getattr(settings, 'ENFORCE_MFA_FOR_PAYROLL', False):
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        if not can_access_payroll(user):
            return True
        return bool(user.mfa_enabled)


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


class IsPayrollUser(BasePermission):
    def has_permission(self, request, view):
        return can_access_payroll(request.user)


class IsPayrollManager(BasePermission):
    def has_permission(self, request, view):
        return can_manage_payroll(request.user)


class CanManageReports(BasePermission):
    def has_permission(self, request, view):
        return can_manage_reports(request.user)


class CanApproveAttendance(BasePermission):
    def has_permission(self, request, view):
        return can_approve_attendance(request.user)


class HasPermission(BasePermission):
    """Check a single permission codename on the view."""

    def has_permission(self, request, view):
        permission = getattr(view, 'required_permission', None)
        if not permission:
            return True
        return user_has_permission(request.user, permission)


class HasAPIKeyScope(BasePermission):
    """When authenticated via API key, require one of view.required_api_scopes."""

    message = 'API key lacks required scope.'

    def has_permission(self, request, view):
        api_key = getattr(request, 'auth_api_key', None)
        if api_key is None:
            return True  # session auth — scopes not applicable
        required = getattr(view, 'required_api_scopes', None) or []
        if not required:
            return True
        scopes = set(api_key.scopes or [])
        if 'admin' in scopes:
            return True
        return any(scope in scopes for scope in required)


def permission_required(permission):
    class _Permission(BasePermission):
        def has_permission(self, request, view):
            return user_has_permission(request.user, permission)

    return _Permission

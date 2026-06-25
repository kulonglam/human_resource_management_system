from rest_framework.permissions import BasePermission, SAFE_METHODS


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

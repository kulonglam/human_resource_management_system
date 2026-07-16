from accounts.access_control import can_access_employee, get_user_accessible_employees
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from .audit import log_action


class AuditLogMixin:
    """Log create, update, and delete operations to the audit trail."""

    audit_writes = True

    def _audit_model(self):
        if getattr(self, 'queryset', None) is not None:
            return self.queryset.model
        return self.serializer_class.Meta.model

    def _audit_description(self, response_data, obj_id):
        if not isinstance(response_data, dict):
            return str(obj_id)
        for key in ('full_name', 'name', 'title', 'description', 'username', 'email'):
            if response_data.get(key):
                return str(response_data[key])[:255]
        return str(obj_id)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if self.audit_writes and response.status_code == 201:
            obj_id = response.data.get('id') if isinstance(response.data, dict) else None
            if obj_id:
                log_action(
                    request,
                    'create',
                    self._audit_model().__name__,
                    obj_id,
                    self._audit_description(response.data, obj_id),
                )
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if self.audit_writes and response.status_code == 200:
            obj_id = response.data.get('id') if isinstance(response.data, dict) else kwargs.get('pk')
            if obj_id:
                log_action(
                    request,
                    'update',
                    self._audit_model().__name__,
                    obj_id,
                    self._audit_description(response.data, obj_id),
                )
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        model_name = instance.__class__.__name__
        obj_id = instance.pk
        description = str(instance)[:255]
        response = super().destroy(request, *args, **kwargs)
        if self.audit_writes and response.status_code == 204:
            log_action(request, 'delete', model_name, obj_id, description)
        return response


class AuditedModelViewSet(AuditLogMixin, viewsets.ModelViewSet):
    pass


class EmployeeQuerysetMixin:
    """Enforce employee scope for both reads and writes."""

    employee_field = 'employee'

    def get_accessible_employee_ids(self):
        return get_user_accessible_employees(self.request.user).values_list('pk', flat=True)

    def filter_by_accessible_employees(self, queryset):
        return queryset.filter(**{f'{self.employee_field}__in': self.get_accessible_employee_ids()})

    def employee_allowed(self, employee):
        return can_access_employee(self.request.user, employee)

    def _validate_employee_write_scope(self, request):
        employee_id = request.data.get(self.employee_field)
        if employee_id in (None, ''):
            return
        try:
            is_allowed = self.get_accessible_employee_ids().filter(pk=employee_id).exists()
        except (TypeError, ValueError):
            is_allowed = False
        if not is_allowed:
            raise PermissionDenied('You cannot modify records for this employee.')

    def create(self, request, *args, **kwargs):
        self._validate_employee_write_scope(request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._validate_employee_write_scope(request)
        return super().update(request, *args, **kwargs)

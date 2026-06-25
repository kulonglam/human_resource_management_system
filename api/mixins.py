from accounts.access_control import can_access_employee, get_user_accessible_employees
from rest_framework import viewsets

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
    """Filter querysets to employees the current user may access."""

    employee_field = 'employee'

    def get_accessible_employee_ids(self):
        return get_user_accessible_employees(self.request.user).values_list('pk', flat=True)

    def filter_by_accessible_employees(self, queryset):
        return queryset.filter(**{f'{self.employee_field}__in': self.get_accessible_employee_ids()})

    def employee_allowed(self, employee):
        return can_access_employee(self.request.user, employee)

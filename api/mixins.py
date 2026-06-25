from accounts.access_control import can_access_employee, get_user_accessible_employees


class EmployeeQuerysetMixin:
    """Filter querysets to employees the current user may access."""

    employee_field = 'employee'

    def get_accessible_employee_ids(self):
        return get_user_accessible_employees(self.request.user).values_list('pk', flat=True)

    def filter_by_accessible_employees(self, queryset):
        return queryset.filter(**{f'{self.employee_field}__in': self.get_accessible_employee_ids()})

    def employee_allowed(self, employee):
        return can_access_employee(self.request.user, employee)

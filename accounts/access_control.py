"""Role-Based Access Control utilities."""

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from accounts.models import Role
from employees.models import Employee


def get_user_permissions(user):
    if not user.is_authenticated:
        return []
    if user.is_admin:
        return Role.ALL_PERMISSIONS
    if user.role:
        return user.role.resolved_permissions()
    return []


def user_has_permission(user, permission):
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    return permission in get_user_permissions(user)


def get_user_accessible_employees(user):
    """
    Get employees accessible by the given user based on their role.

    - Admin: All employees
    - Manager: Employees in their department
    - Employee: Only themselves
    """
    if not hasattr(user, 'role') or not user.role:
        return Employee.objects.none()

    if user.is_admin:
        qs = Employee.objects.all()
        if getattr(user, 'organization_id', None):
            qs = qs.filter(organization_id=user.organization_id)
        return qs

    if user.is_manager:
        qs = Employee.objects.none()
        try:
            manager_emp = Employee.objects.get(email=user.email)
            if manager_emp.department_id:
                qs = Employee.objects.filter(department_id=manager_emp.department_id)
        except Employee.DoesNotExist:
            pass
        if not qs.exists() and getattr(user, 'managed_department_id', None):
            qs = Employee.objects.filter(department_id=user.managed_department_id)
        if getattr(user, 'organization_id', None):
            qs = qs.filter(organization_id=user.organization_id)
        return qs

    try:
        emp = Employee.objects.get(email=user.email)
        return Employee.objects.filter(pk=emp.pk)
    except Employee.DoesNotExist:
        return Employee.objects.none()


def can_access_employee(user, employee):
    """Check if user has permission to access a specific employee."""
    accessible = get_user_accessible_employees(user)
    return accessible.filter(pk=employee.pk).exists()


def can_access_payroll(user):
    """Check if user has permission to access payroll data."""
    return user.is_authenticated and (
        user.is_admin or user_has_permission(user, Role.PERMISSION_PAYROLL_VIEW)
    )


def can_manage_payroll(user):
    return user.is_authenticated and (
        user.is_admin or user_has_permission(user, Role.PERMISSION_PAYROLL_MANAGE)
    )


def can_view_sensitive_data(user):
    return user.is_authenticated and (
        user.is_admin or user_has_permission(user, Role.PERMISSION_SENSITIVE_VIEW)
    )


def can_manage_reports(user):
    return user.is_authenticated and (
        user.is_admin or user_has_permission(user, Role.PERMISSION_REPORTS_MANAGE)
    )


def can_approve_attendance(user):
    return user.is_authenticated and (
        user.is_admin or user_has_permission(user, Role.PERMISSION_ATTENDANCE_APPROVE)
    )


def can_approve_leaves(user):
    """Check if user can approve leave requests."""
    return user.is_authenticated and (user.is_admin or user.is_manager)


def mask_sensitive_value(value):
    if not value:
        return value
    text = str(value)
    if len(text) <= 4:
        return '****'
    return f'{"*" * (len(text) - 4)}{text[-4:]}'

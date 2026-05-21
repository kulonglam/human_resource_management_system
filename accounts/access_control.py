# accounts/access_control.py
"""Role-Based Access Control utilities."""

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from employees.models import Employee


def get_user_accessible_employees(user):
    """
    Get employees accessible by the given user based on their role.
    
    - Admin: All employees
    - Manager: Employees in their department (or all if no department assigned)
    - Employee: Only themselves
    """
    if not hasattr(user, 'role') or not user.role:
        return Employee.objects.none()
    
    if user.is_admin:
        return Employee.objects.all()
    
    if user.is_manager:
        # Try to get manager's employee record to access their department
        try:
            manager_emp = Employee.objects.get(email=user.email)
            if manager_emp.department:
                return Employee.objects.filter(department=manager_emp.department)
            return Employee.objects.all()
        except Employee.DoesNotExist:
            return Employee.objects.all()
    
    # Employee - only see themselves
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
    return user.is_authenticated and (user.is_admin or user.is_manager)


def can_approve_leaves(user):
    """Check if user can approve leave requests."""
    return user.is_authenticated and (user.is_admin or user.is_manager)

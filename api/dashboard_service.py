from datetime import timedelta

from django.db.models import Sum, F
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from employees.models import Employee
from expenses.models import Expense
from leaves.models import Leave
from payroll.models import Salary
from recruitment.models import Application, JobPosting
from workflows.services import get_pending_for_user


def resolve_dashboard_role(user):
    if user.is_admin:
        return 'hr'
    if user.is_manager:
        return 'manager'
    return 'employee'


def build_role_dashboard(user, base_data):
    role = resolve_dashboard_role(user)
    today = timezone.now().date()
    month = today.month
    year = today.year

    role_data = {
        'dashboard_role': role,
        'pending_approvals': get_pending_for_user(user).count() if (user.is_admin or user.is_manager) else 0,
    }

    if role == 'employee':
        role_data['highlights'] = [
            {'label': 'Leave balances', 'value': len(base_data.get('user_leave_balances', [])), 'link': '/leaves'},
            {'label': 'Active goals', 'value': base_data.get('active_goals', 0), 'link': '/performance'},
            {'label': 'Training courses', 'value': base_data.get('active_courses', 0), 'link': '/training'},
        ]
        return role_data

    if role == 'manager':
        role_data['highlights'] = [
            {'label': 'Team size', 'value': base_data.get('dept_leave_summary', {}).get('employee_count', 0), 'link': '/employees'},
            {'label': 'Pending leaves', 'value': base_data.get('pending_leaves', 0), 'link': '/leaves'},
            {'label': 'Pending approvals', 'value': role_data['pending_approvals'], 'link': '/leaves'},
            {'label': 'Open jobs', 'value': base_data.get('open_jobs', 0), 'link': '/recruitment'},
        ]
        return role_data

    payroll = Salary.objects.filter(month=month, year=year)
    role_data['exec_summary'] = {
        'headcount': Employee.objects.filter(is_active=True).count(),
        'new_joiners_30d': Employee.objects.filter(
            date_joined__gte=today - timedelta(days=30), is_active=True,
        ).count(),
        'monthly_payroll_net': payroll.aggregate(total=Sum('net_salary'))['total'] or 0,
        'open_positions': JobPosting.objects.filter(is_open=True).count(),
        'pending_applications': Application.objects.filter(status='received').count(),
        'pending_expenses': Expense.objects.filter(status='submitted').count(),
    }
    role_data['highlights'] = [
        {'label': 'Employees', 'value': base_data.get('total_employees', 0), 'link': '/employees'},
        {'label': 'Pending leaves', 'value': base_data.get('pending_leaves', 0), 'link': '/leaves'},
        {'label': 'Pending approvals', 'value': role_data['pending_approvals'], 'link': '/leaves'},
        {'label': 'Departments', 'value': base_data.get('total_departments', 0), 'link': '/org-chart'},
    ]
    return role_data

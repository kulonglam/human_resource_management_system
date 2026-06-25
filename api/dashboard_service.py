from datetime import date, timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from accounts.models import AuditLog
from employees.models import Employee
from expenses.models import Expense
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from recruitment.models import Application, JobPosting
from training.models import EmployeeCertification
from workflows.services import get_pending_for_user


def resolve_dashboard_role(user):
    if user.is_admin:
        return 'hr'
    if user.is_manager:
        return 'manager'
    return 'employee'


def _last_n_months(n=6):
    today = timezone.now().date()
    year, month = today.year, today.month
    months = []
    for _ in range(n):
        months.append({'year': year, 'month': month, 'label': date(year, month, 1).strftime('%b %Y')})
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


def _month_end(year, month):
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _headcount_on(day):
    return Employee.objects.filter(date_joined__lte=day).filter(
        Q(termination_date__isnull=True) | Q(termination_date__gt=day),
    ).count()


def _metric_delta(current, previous):
    current = current or 0
    previous = previous if previous is not None else 0
    change = current - previous
    if previous == 0:
        pct = 100.0 if change > 0 else 0.0 if change == 0 else None
    else:
        pct = round((change / previous) * 100, 1)
    direction = 'up' if change > 0 else 'down' if change < 0 else 'flat'
    return {'change': change, 'change_pct': pct, 'direction': direction, 'previous': previous}


def _approval_summary(req):
    target = req.content_object
    if target is None:
        return f'Item #{req.object_id}'
    workflow_type = req.workflow.workflow_type
    if workflow_type == 'leave':
        return (
            f'{target.employee.full_name} — {target.get_leave_type_display()} '
            f'({target.start_date} to {target.end_date})'
        )
    if workflow_type == 'expense':
        return f'{target.employee.full_name} — {target.description} (KES {target.amount})'
    if workflow_type == 'recruitment':
        return f'{target.first_name} {target.last_name} — {target.job.title}'
    return str(target)


def build_headcount_series(months=12):
    points = []
    for entry in _last_n_months(months):
        end = _month_end(entry['year'], entry['month'])
        short = date(entry['year'], entry['month'], 1).strftime('%b')
        points.append({
            'label': short,
            'full_label': entry['label'],
            'value': _headcount_on(end),
        })
    return points


def build_payroll_series(months=12):
    points = []
    for entry in _last_n_months(months):
        total = Salary.objects.filter(
            month=entry['month'], year=entry['year'],
        ).aggregate(total=Sum('net_salary'))['total'] or 0
        short = date(entry['year'], entry['month'], 1).strftime('%b')
        points.append({
            'label': short,
            'full_label': entry['label'],
            'value': float(total),
        })
    return points


def build_leave_series(months=6):
    points = []
    for entry in _last_n_months(months):
        leaves = Leave.objects.filter(
            status='approved',
            start_date__year=entry['year'],
            start_date__month=entry['month'],
        )
        total_days = sum(leave.duration for leave in leaves)
        short = date(entry['year'], entry['month'], 1).strftime('%b')
        points.append({'label': short, 'full_label': entry['label'], 'value': float(total_days)})
    return points


def build_recruitment_funnel():
    stages = [
        ('received', 'Received'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('hired', 'Hired'),
    ]
    apps = Application.objects.all()
    total = apps.count() or 1
    return {
        'title': 'Hiring pipeline',
        'stages': [
            {
                'key': key,
                'label': label,
                'count': apps.filter(status=key).count(),
                'pct': round((apps.filter(status=key).count() / total) * 100, 1),
            }
            for key, label in stages
        ],
        'open_positions': JobPosting.objects.filter(is_open=True).count(),
        'total_applications': apps.count(),
    }


def build_employee_leave_chart(balances):
    if not balances:
        return None
    return {
        'title': 'Your leave usage',
        'subtitle': 'Days used vs allocated this year',
        'points': [
            {'label': b['leave_type_display'], 'value': b['used_days'], 'max': b['total_days']}
            for b in balances
        ],
    }


def build_dept_leave_chart(summary):
    if not summary:
        return None
    return {
        'title': 'Department leave overview',
        'subtitle': 'Team leave days this year',
        'points': [
            {'label': 'Used', 'value': summary['total_used']},
            {'label': 'Pending', 'value': summary['total_pending']},
            {'label': 'Available', 'value': summary['total_available']},
        ],
    }


def build_chart_data(role, base_data):
    if role == 'employee':
        return build_employee_leave_chart(base_data.get('user_leave_balances', []))
    if role == 'manager':
        return build_dept_leave_chart(base_data.get('dept_leave_summary')) or {
            'title': 'Team leave trend',
            'subtitle': 'Approved leave days (6 months)',
            'points': build_leave_series(6),
        }
    return {
        'title': 'New joiners (6 months)',
        'subtitle': 'Monthly onboarding volume',
        'points': [
            {
                'label': date(e['year'], e['month'], 1).strftime('%b'),
                'value': Employee.objects.filter(
                    date_joined__year=e['year'], date_joined__month=e['month'],
                ).count(),
            }
            for e in _last_n_months(6)
        ],
    }


def build_attention_items(user, role, base_data, role_data):
    items = []
    pending_approvals = role_data.get('pending_approvals', 0)
    if pending_approvals:
        items.append({
            'severity': 'critical' if pending_approvals >= 5 else 'warning',
            'message': f'{pending_approvals} approval{"s" if pending_approvals != 1 else ""} awaiting decision',
            'link': '/approvals',
            'icon': 'bi-inbox',
        })

    pending_leaves = base_data.get('pending_leaves', 0)
    if pending_leaves and role in ('hr', 'manager'):
        items.append({
            'severity': 'warning',
            'message': f'{pending_leaves} leave request{"s" if pending_leaves != 1 else ""} pending review',
            'link': '/leaves',
            'icon': 'bi-calendar-x',
        })

    if role == 'hr':
        exec_summary = role_data.get('exec_summary') or {}
        pending_expenses = exec_summary.get('pending_expenses', 0)
        if pending_expenses:
            items.append({
                'severity': 'warning',
                'message': f'{pending_expenses} expense claim{"s" if pending_expenses != 1 else ""} awaiting approval',
                'link': '/expenses',
                'icon': 'bi-receipt',
            })
        expiring = base_data.get('expiring_certifications', 0)
        if expiring:
            items.append({
                'severity': 'info',
                'message': f'{expiring} certification{"s" if expiring != 1 else ""} expiring within 30 days',
                'link': '/training',
                'icon': 'bi-award',
            })
        pending_apps = exec_summary.get('pending_applications', 0)
        if pending_apps:
            items.append({
                'severity': 'info',
                'message': f'{pending_apps} new application{"s" if pending_apps != 1 else ""} to review',
                'link': '/recruitment',
                'icon': 'bi-briefcase',
            })

    if role == 'employee':
        try:
            employee = Employee.objects.get(email=user.email)
            pending_own = Leave.objects.filter(employee=employee, status='pending').count()
            if pending_own:
                items.append({
                    'severity': 'info',
                    'message': f'{pending_own} of your leave request{"s" if pending_own != 1 else ""} pending',
                    'link': '/leaves',
                    'icon': 'bi-hourglass-split',
                })
        except Employee.DoesNotExist:
            pass

    return items[:6]


def build_exec_brief(role, base_data, role_data):
    if role != 'hr':
        return None

    exec_summary = role_data.get('exec_summary') or {}
    headcount = exec_summary.get('headcount', base_data.get('total_employees', 0))
    joiners = exec_summary.get('new_joiners_30d', 0)
    payroll = int(exec_summary.get('monthly_payroll_net', 0) or 0)
    open_roles = exec_summary.get('open_positions', base_data.get('open_jobs', 0))
    pending_leaves = base_data.get('pending_leaves', 0)
    pending_approvals = role_data.get('pending_approvals', 0)

    sentences = [
        f'Active workforce: {headcount} employees across {base_data.get("total_departments", 0)} departments.',
    ]
    if joiners:
        sentences.append(f'{joiners} new joiner{"s" if joiners != 1 else ""} in the last 30 days.')
    if payroll:
        sentences.append(f'Current-month payroll outflow: KES {payroll:,} (net).')
    if open_roles:
        sentences.append(f'{open_roles} open position{"s" if open_roles != 1 else ""} in the hiring pipeline.')
    if pending_approvals or pending_leaves:
        sentences.append(
            f'Action queue: {pending_approvals} approval{"s" if pending_approvals != 1 else ""} '
            f'and {pending_leaves} leave request{"s" if pending_leaves != 1 else ""} need attention.'
        )
    else:
        sentences.append('Approval and leave queues are clear.')

    return ' '.join(sentences)


def build_hero_kpis(role, base_data, role_data):
    today = timezone.now().date()
    exec_summary = role_data.get('exec_summary') or {}

    if role == 'employee':
        balances = base_data.get('user_leave_balances', [])
        available = sum(b['available_days'] for b in balances)
        return [
            {'label': 'Leave available', 'value': f'{available:.1f} days', 'icon': 'bi-calendar-check', 'link': '/leaves'},
            {'label': 'Active goals', 'value': base_data.get('active_goals', 0), 'icon': 'bi-bullseye', 'link': '/performance'},
            {'label': 'Training courses', 'value': base_data.get('active_courses', 0), 'icon': 'bi-book', 'link': '/training'},
            {'label': 'Appraisals', 'value': base_data.get('total_appraisals', 0), 'icon': 'bi-graph-up', 'link': '/performance'},
        ]

    if role == 'manager':
        dept = base_data.get('dept_leave_summary') or {}
        team_size = dept.get('employee_count', 0)
        return [
            {'label': 'Team size', 'value': team_size, 'icon': 'bi-people', 'link': '/employees'},
            {
                'label': 'Pending approvals', 'value': role_data.get('pending_approvals', 0),
                'icon': 'bi-inbox', 'link': '/approvals',
            },
            {
                'label': 'Pending leaves', 'value': base_data.get('pending_leaves', 0),
                'icon': 'bi-calendar-x', 'link': '/leaves',
            },
            {
                'label': 'Open jobs', 'value': base_data.get('open_jobs', 0),
                'icon': 'bi-briefcase', 'link': '/recruitment',
            },
        ]

    headcount = exec_summary.get('headcount', base_data.get('total_employees', 0))
    prev_month = _last_n_months(2)[0]
    prev_hc = _headcount_on(_month_end(prev_month['year'], prev_month['month']))

    payroll = int(exec_summary.get('monthly_payroll_net', 0) or 0)
    prev_payroll_month = _last_n_months(2)[0]
    prev_payroll = Salary.objects.filter(
        month=prev_payroll_month['month'], year=prev_payroll_month['year'],
    ).aggregate(total=Sum('net_salary'))['total'] or 0

    joiners_30 = exec_summary.get('new_joiners_30d', 0)
    joiners_prev_30 = Employee.objects.filter(
        date_joined__gte=today - timedelta(days=60),
        date_joined__lt=today - timedelta(days=30),
        is_active=True,
    ).count()

    return [
        {
            'label': 'Headcount', 'value': headcount, 'icon': 'bi-people-fill', 'link': '/employees',
            'delta': _metric_delta(headcount, prev_hc),
        },
        {
            'label': 'New joiners (30d)', 'value': joiners_30, 'icon': 'bi-person-plus', 'link': '/employees',
            'delta': _metric_delta(joiners_30, joiners_prev_30),
        },
        {
            'label': 'Pending approvals', 'value': role_data.get('pending_approvals', 0),
            'icon': 'bi-inbox', 'link': '/approvals',
        },
        {
            'label': 'Payroll (net)', 'value': f'KES {payroll:,}', 'icon': 'bi-cash-stack', 'link': '/payroll',
            'delta': _metric_delta(payroll, int(prev_payroll)),
        },
    ]


def build_pending_items(user, role, limit=5):
    items = []

    if role in ('hr', 'manager'):
        for req in get_pending_for_user(user).select_related('workflow', 'content_type')[:limit]:
            items.append({
                'id': req.pk,
                'type': req.workflow.workflow_type,
                'title': req.workflow.name,
                'summary': _approval_summary(req),
                'submitted_at': req.submitted_at.isoformat() if req.submitted_at else None,
                'link': '/approvals',
            })
        return items

    try:
        employee = Employee.objects.get(email=user.email)
    except Employee.DoesNotExist:
        return items

    for leave in Leave.objects.filter(employee=employee, status='pending').order_by('-applied_on')[:limit]:
        items.append({
            'id': leave.pk,
            'type': 'leave',
            'title': 'Leave request pending',
            'summary': (
                f'{leave.get_leave_type_display()} — {leave.start_date} to {leave.end_date} '
                f'({leave.duration} days)'
            ),
            'submitted_at': leave.applied_on.isoformat() if leave.applied_on else None,
            'link': '/leaves',
        })
    return items


def build_recent_activity(user, role, limit=8):
    if role not in ('hr', 'manager'):
        return []

    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:limit]
    return [
        {
            'id': log.pk,
            'action': log.action,
            'model_name': log.model_name,
            'description': log.object_description or str(log.object_id or ''),
            'username': log.user.username if log.user else 'System',
            'timestamp': log.timestamp.isoformat(),
        }
        for log in logs
    ]


def build_workforce_snapshot(base_data):
    leave = base_data.get('all_leave_summary') or {}
    return {
        'active_goals': base_data.get('active_goals', 0),
        'total_goals': base_data.get('total_goals', 0),
        'total_appraisals': base_data.get('total_appraisals', 0),
        'active_courses': base_data.get('active_courses', 0),
        'expiring_certifications': base_data.get('expiring_certifications', 0),
        'leave_allocated': leave.get('total_allocated'),
        'leave_used': leave.get('total_used'),
        'leave_available': leave.get('total_available'),
    }


def build_role_dashboard(user, base_data):
    role = resolve_dashboard_role(user)
    today = timezone.now().date()
    month = today.month
    year = today.year

    role_data = {
        'dashboard_role': role,
        'as_of': timezone.now().isoformat(),
        'pending_approvals': get_pending_for_user(user).count() if (user.is_admin or user.is_manager) else 0,
    }

    if role == 'employee':
        role_data['highlights'] = [
            {'label': 'Leave balances', 'value': len(base_data.get('user_leave_balances', [])), 'link': '/leaves'},
            {'label': 'Active goals', 'value': base_data.get('active_goals', 0), 'link': '/performance'},
            {'label': 'Training courses', 'value': base_data.get('active_courses', 0), 'link': '/training'},
        ]
    elif role == 'manager':
        role_data['highlights'] = [
            {'label': 'Team size', 'value': base_data.get('dept_leave_summary', {}).get('employee_count', 0), 'link': '/employees'},
            {'label': 'Pending leaves', 'value': base_data.get('pending_leaves', 0), 'link': '/leaves'},
            {'label': 'Pending approvals', 'value': role_data['pending_approvals'], 'link': '/approvals'},
            {'label': 'Open jobs', 'value': base_data.get('open_jobs', 0), 'link': '/recruitment'},
        ]
    else:
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
            {'label': 'Pending approvals', 'value': role_data['pending_approvals'], 'link': '/approvals'},
            {'label': 'Departments', 'value': base_data.get('total_departments', 0), 'link': '/org-chart'},
        ]

    role_data['hero_kpis'] = build_hero_kpis(role, base_data, role_data)
    role_data['chart'] = build_chart_data(role, base_data)
    role_data['attention_items'] = build_attention_items(user, role, base_data, role_data)
    role_data['exec_brief'] = build_exec_brief(role, base_data, role_data)
    role_data['pending_items'] = build_pending_items(user, role)
    role_data['recent_activity'] = build_recent_activity(user, role)
    role_data['workforce_snapshot'] = build_workforce_snapshot(base_data) if role == 'hr' else None

    if role == 'hr':
        role_data['exec_analytics'] = {
            'headcount_trend': {
                'title': 'Workforce headcount',
                'subtitle': 'Active employees at month end (12 months)',
                'points': build_headcount_series(12),
            },
            'payroll_trend': {
                'title': 'Payroll outflow',
                'subtitle': 'Net salary paid per month (KES)',
                'points': build_payroll_series(12),
            },
            'leave_trend': {
                'title': 'Leave utilisation',
                'subtitle': 'Approved leave days per month',
                'points': build_leave_series(6),
            },
            'recruitment_funnel': build_recruitment_funnel(),
        }
    elif role == 'manager':
        role_data['exec_analytics'] = {
            'leave_trend': {
                'title': 'Organisation leave trend',
                'subtitle': 'Approved leave days (6 months)',
                'points': build_leave_series(6),
            },
        }

    return role_data

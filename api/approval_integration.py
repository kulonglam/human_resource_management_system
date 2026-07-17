from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser

from .audit import log_action
from .in_app_notifications import get_hr_users, get_manager_users_for_employee, notify_user, notify_users
from workflows.services import (
    get_pending_for_user,
    get_request_for_object,
    process_decision,
    start_approval,
    user_can_approve,
)


def _notify_next_approvers(obj, approval_request, title, link='/approvals'):
    from workflows.services import _current_step

    step = _current_step(approval_request)
    if not step:
        return
    if step.approver_type == 'admin':
        notify_users(get_hr_users(), title, f'Your review is required: {title}', 'approval', link)
    elif step.approver_type == 'manager' and hasattr(obj, 'employee'):
        notify_users(
            get_manager_users_for_employee(obj.employee),
            title,
            f'Your review is required: {title}',
            'approval',
            link,
        )


def _notify_submitter(submitted_by, title, message, link, category='approval'):
    if submitted_by:
        notify_user(submitted_by, title, message, category, link)


def start_leave_approval(leave, user):
    approval = start_approval('leave', leave, user, context={'duration': leave.duration})
    if approval:
        _notify_next_approvers(
            leave,
            approval,
            f'Leave request — {leave.employee.full_name}',
            '/approvals',
        )
    return approval


def start_expense_approval(expense, user):
    approval = start_approval('expense', expense, user, context={'amount': expense.amount})
    if approval:
        _notify_next_approvers(
            expense,
            approval,
            f'Expense claim — {expense.employee.full_name}',
            '/approvals',
        )
    return approval


def start_recruitment_approval(application, user):
    approval = start_approval('recruitment', application, user)
    if approval:
        recipients = list(get_hr_users())
        manager_ids = {u.pk for u in recipients}
        for manager in CustomUser.objects.filter(role__name='manager', is_active=True):
            if manager.pk not in manager_ids:
                recipients.append(manager)
                manager_ids.add(manager.pk)
        notify_users(
            recipients,
            f'Application review — {application.first_name} {application.last_name}',
            f'Review required for {application.job.title}',
            'approval',
            '/approvals',
        )
    return approval


def process_leave_decision(request, leave, approved, comment=''):
    from leaves.models import LeaveBalance

    approval = get_request_for_object(leave)
    if approval and approval.status == 'pending':
        outcome = process_decision(approval, request.user, approved, comment)
        if outcome['result'] == 'denied':
            return {'status': 403, 'detail': outcome['detail']}
        if outcome['result'] == 'rejected':
            _reject_leave(request, leave, comment)
            _notify_submitter(
                approval.submitted_by,
                'Leave request rejected',
                f'Your leave request was rejected at {outcome["step"]}.',
                '/leaves',
                'leave',
            )
            return {'status': 200, 'result': 'rejected'}
        if outcome['result'] == 'advanced':
            log_action(
                request, 'approve', 'Leave', leave.id, str(leave),
                f'Leave approved at {outcome["step"]}; pending {outcome["next_step"]}',
            )
            _notify_next_approvers(
                leave, approval,
                f'Leave request — {leave.employee.full_name}',
                '/approvals',
            )
            _notify_submitter(
                approval.submitted_by,
                'Leave request progressed',
                f'Approved at {outcome["step"]}. Pending {outcome["next_step"]}.',
                '/leaves',
                'leave',
            )
            return {'status': 200, 'result': 'advanced'}
        if outcome['result'] == 'approved':
            _finalize_leave_approval(request, leave)
            _notify_submitter(
                approval.submitted_by,
                'Leave request approved',
                'Your leave request has been fully approved.',
                '/leaves',
                'leave',
            )
            return {'status': 200, 'result': 'approved'}

    if not approved:
        _reject_leave(request, leave, comment)
        return {'status': 200, 'result': 'rejected'}

    _finalize_leave_approval(request, leave)
    return {'status': 200, 'result': 'approved'}


def _finalize_leave_approval(request, leave):
    from leaves.models import LeaveBalance

    with transaction.atomic():
        leave = leave.__class__.objects.select_for_update().select_related('employee').get(pk=leave.pk)
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.select_for_update().get(
                employee=leave.employee, leave_type=leave.leave_type, year=current_year,
            )
            balance.pending_days = max(float(balance.pending_days) - float(leave.working_days), 0.0)
            balance.used_days = float(balance.used_days) + float(leave.working_days)
            balance.save(update_fields=['pending_days', 'used_days'])
        except LeaveBalance.DoesNotExist:
            pass
        leave.status = 'approved'
        leave.reviewed_by = request.user.get_full_name() or request.user.username
        leave.reviewed_on = timezone.now()
        leave.save(update_fields=['status', 'reviewed_by', 'reviewed_on', 'working_days'])
    log_action(request, 'approve', 'Leave', leave.id, str(leave), 'Leave fully approved')
    from integrations.services import dispatch_webhook
    dispatch_webhook('leave.approved', {
        'id': leave.id,
        'employee_id': leave.employee_id,
        'employee_name': leave.employee.full_name,
        'leave_type': leave.leave_type,
        'start_date': str(leave.start_date),
        'end_date': str(leave.end_date),
    })


def _reject_leave(request, leave, comment=''):
    from leaves.models import LeaveBalance

    with transaction.atomic():
        leave = leave.__class__.objects.select_for_update().select_related('employee').get(pk=leave.pk)
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.select_for_update().get(
                employee=leave.employee, leave_type=leave.leave_type, year=current_year,
            )
            balance.pending_days = max(float(balance.pending_days) - float(leave.working_days), 0.0)
            balance.save(update_fields=['pending_days'])
        except LeaveBalance.DoesNotExist:
            pass
        leave.status = 'rejected'
        leave.reviewed_by = request.user.get_full_name() or request.user.username
        leave.reviewed_on = timezone.now()
        leave.save(update_fields=['status', 'reviewed_by', 'reviewed_on', 'working_days'])
    log_action(request, 'reject', 'Leave', leave.id, str(leave), comment or 'Leave rejected')
    from integrations.services import dispatch_webhook
    dispatch_webhook('leave.rejected', {
        'id': leave.id,
        'employee_id': leave.employee_id,
        'employee_name': leave.employee.full_name,
        'reason': comment,
    })


def process_expense_decision(request, expense, approved, comment=''):
    approval = get_request_for_object(expense)
    if approval and approval.status == 'pending':
        outcome = process_decision(approval, request.user, approved, comment)
        if outcome['result'] == 'denied':
            return {'status': 403, 'detail': outcome['detail']}
        if outcome['result'] == 'rejected':
            _reject_expense(request, expense, comment)
            return {'status': 200, 'result': 'rejected'}
        if outcome['result'] == 'advanced':
            log_action(
                request, 'approve', 'Expense', expense.id, expense.description,
                f'Expense approved at {outcome["step"]}; pending {outcome["next_step"]}',
            )
            _notify_next_approvers(
                expense, approval,
                f'Expense — {expense.employee.full_name}',
                '/approvals',
            )
            return {'status': 200, 'result': 'advanced'}
        if outcome['result'] == 'approved':
            _finalize_expense_approval(request, expense)
            return {'status': 200, 'result': 'approved'}

    if not approved:
        _reject_expense(request, expense, comment)
        return {'status': 200, 'result': 'rejected'}
    _finalize_expense_approval(request, expense)
    return {'status': 200, 'result': 'approved'}


def _finalize_expense_approval(request, expense):
    from expenses.services import finalize_expense_approval

    expense = finalize_expense_approval(expense=expense)
    log_action(request, 'approve', 'Expense', expense.id, expense.description, 'Expense fully approved')
    from integrations.services import dispatch_webhook
    dispatch_webhook('expense.approved', {
        'id': expense.id,
        'employee_id': expense.employee_id,
        'amount': str(expense.amount),
        'description': expense.description,
    })


def _reject_expense(request, expense, comment=''):
    from expenses.services import reject_expense

    expense = reject_expense(expense=expense, reason=comment)
    log_action(request, 'reject', 'Expense', expense.id, expense.description, comment or 'Expense rejected')
    from integrations.services import dispatch_webhook
    dispatch_webhook('expense.rejected', {
        'id': expense.id,
        'employee_id': expense.employee_id,
        'amount': str(expense.amount),
        'reason': comment,
    })


def process_recruitment_decision(request, application, approved, comment=''):
    approval = get_request_for_object(application)
    if not approval:
        approval = start_recruitment_approval(application, request.user)

    if approval and approval.status == 'pending':
        outcome = process_decision(approval, request.user, approved, comment)
        if outcome['result'] == 'denied':
            return {'status': 403, 'detail': outcome['detail']}
        if outcome['result'] == 'rejected':
            _reject_recruitment(request, application, comment)
            return {'status': 200, 'result': 'rejected'}
        if outcome['result'] == 'advanced':
            log_action(
                request, 'approve', 'Application', application.id, str(application),
                f'Advanced to {outcome["next_step"]}',
            )
            _notify_next_approvers(
                application, approval,
                f'Application — {application.first_name} {application.last_name}',
                '/approvals',
            )
            return {'status': 200, 'result': 'advanced'}
        if outcome['result'] == 'approved':
            _finalize_recruitment_approval(request, application)
            return {'status': 200, 'result': 'approved'}

    if not approved:
        _reject_recruitment(request, application, comment)
        return {'status': 200, 'result': 'rejected'}
    _finalize_recruitment_approval(request, application)
    return {'status': 200, 'result': 'approved'}


def _reject_recruitment(request, application, comment=''):
    with transaction.atomic():
        application = application.__class__.objects.select_for_update().get(pk=application.pk)
        application.status = 'rejected'
        application.save(update_fields=['status'])
    log_action(request, 'reject', 'Application', application.id, str(application), comment)


def _finalize_recruitment_approval(request, application):
    from recruitment.services import create_hire_onboarding, sync_application_stage

    with transaction.atomic():
        application = application.__class__.objects.select_for_update().select_related('job').get(
            pk=application.pk,
        )
        if application.status == 'received':
            stage = application.job.pipeline_stages.filter(key='shortlisted').first()
            if stage:
                sync_application_stage(application, stage)
            else:
                application.status = 'shortlisted'
                application.save(update_fields=['status'])
        elif application.status in ('shortlisted', 'interviewed', 'offer'):
            stage = application.job.pipeline_stages.filter(stage_type='hired').first()
            if stage:
                sync_application_stage(application, stage)
            else:
                application.status = 'hired'
                application.hired_at = timezone.now()
                application.save(update_fields=['status', 'hired_at'])
            create_hire_onboarding(application)
    log_action(request, 'approve', 'Application', application.id, str(application), 'Recruitment approved')


def process_approval_request_decision(http_request, approval_request, approved, comment=''):
    obj = approval_request.content_object
    if obj is None:
        return {'status': 404, 'detail': 'Referenced item no longer exists.'}

    workflow_type = approval_request.workflow.workflow_type
    if workflow_type == 'leave':
        return process_leave_decision(http_request, obj, approved, comment)
    if workflow_type == 'expense':
        return process_expense_decision(http_request, obj, approved, comment)
    if workflow_type == 'recruitment':
        return process_recruitment_decision(http_request, obj, approved, comment)
    return {'status': 400, 'detail': f'Unsupported workflow type: {workflow_type}'}

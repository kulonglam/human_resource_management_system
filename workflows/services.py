from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import CustomUser, Role
from employees.models import Employee

from .models import ApprovalDecision, ApprovalRequest, ApprovalStep, ApprovalWorkflow


def _get_default_workflow(workflow_type):
    return ApprovalWorkflow.objects.filter(
        workflow_type=workflow_type, is_default=True, is_active=True,
    ).prefetch_related('steps').first()


def _applicable_steps(workflow, context=None):
    context = context or {}
    steps = list(workflow.steps.order_by('step_order'))
    if not steps:
        return steps

    min_days = workflow.extra_step_min_days
    min_amount = workflow.extra_step_min_amount
    duration = Decimal(str(context.get('duration', 0)))
    amount = Decimal(str(context.get('amount', 0)))

    if min_days is not None and duration < min_days:
        steps = [s for s in steps if s.approver_type != 'admin']
    if min_amount is not None and amount < min_amount:
        steps = [s for s in steps if s.approver_type != 'admin']
    return steps or list(workflow.steps.order_by('step_order'))


def get_request_for_object(obj):
    ct = ContentType.objects.get_for_model(obj)
    return ApprovalRequest.objects.filter(
        content_type=ct, object_id=obj.pk,
    ).select_related('workflow').prefetch_related('decisions').order_by('-submitted_at').first()


def start_approval(workflow_type, obj, user, context=None):
    workflow = _get_default_workflow(workflow_type)
    if not workflow:
        return None

    steps = _applicable_steps(workflow, context)
    if not steps:
        return None

    ct = ContentType.objects.get_for_model(obj)
    existing = ApprovalRequest.objects.filter(
        content_type=ct, object_id=obj.pk, status='pending',
    ).first()
    if existing:
        return existing

    return ApprovalRequest.objects.create(
        workflow=workflow,
        content_type=ct,
        object_id=obj.pk,
        status='pending',
        current_step_order=steps[0].step_order,
        submitted_by=user if user and user.is_authenticated else None,
    )


def _current_step(request):
    steps = _applicable_steps(request.workflow, _request_context(request))
    for step in steps:
        if step.step_order >= request.current_step_order:
            decided = request.decisions.filter(step_order=step.step_order).exists()
            if not decided:
                return step
    return None


def _request_context(request):
    obj = request.content_object
    if obj is None:
        return {}
    if hasattr(obj, 'duration'):
        return {'duration': obj.duration}
    if hasattr(obj, 'amount'):
        return {'amount': obj.amount}
    return {}


def _employee_for_object(obj):
    if hasattr(obj, 'employee'):
        return obj.employee
    if hasattr(obj, 'job'):
        return None
    return None


def user_can_approve(user, approval_request):
    if not user or not user.is_authenticated:
        return False
    if approval_request.status != 'pending':
        return False

    step = _current_step(approval_request)
    if not step:
        return False

    if step.approver_type == 'admin':
        return user.is_admin

    if step.approver_type == 'manager':
        if user.is_admin:
            return True
        if not user.is_manager:
            return False
        employee = _employee_for_object(approval_request.content_object)
        if employee is None:
            return user.is_manager
        try:
            manager_emp = Employee.objects.get(email=user.email)
            return employee.department_id == manager_emp.department_id
        except Employee.DoesNotExist:
            return True

    return False


def get_pending_for_user(user):
    if not user.is_authenticated:
        return ApprovalRequest.objects.none()

    pending = ApprovalRequest.objects.filter(status='pending').select_related(
        'workflow', 'content_type', 'submitted_by',
    )
    ids = [req.pk for req in pending if user_can_approve(user, req)]
    return ApprovalRequest.objects.filter(pk__in=ids)


def process_decision(approval_request, user, approved, comment=''):
    from django.db import transaction

    with transaction.atomic():
        approval_request = ApprovalRequest.objects.select_for_update().select_related(
            'workflow',
        ).prefetch_related('workflow__steps').get(pk=approval_request.pk)

        if approval_request.status != 'pending':
            return {'result': 'invalid', 'detail': 'Request is not pending.'}
        if not user_can_approve(user, approval_request):
            return {'result': 'denied', 'detail': 'You cannot approve this step.'}

        step = _current_step(approval_request)
        if not step:
            return {'result': 'invalid', 'detail': 'No pending approval step.'}

        ApprovalDecision.objects.create(
            request=approval_request,
            step_order=step.step_order,
            step_label=step.label,
            decided_by=user,
            decision='approved' if approved else 'rejected',
            comment=comment,
        )

        if not approved:
            approval_request.status = 'rejected'
            approval_request.completed_at = timezone.now()
            approval_request.save(update_fields=['status', 'completed_at'])
            return {'result': 'rejected', 'step': step.label}

        steps = _applicable_steps(approval_request.workflow, _request_context(approval_request))
        step_orders = [s.step_order for s in steps]
        current_idx = step_orders.index(step.step_order)
        if current_idx + 1 < len(steps):
            next_step = steps[current_idx + 1]
            approval_request.current_step_order = next_step.step_order
            approval_request.save(update_fields=['current_step_order'])
            return {'result': 'advanced', 'step': step.label, 'next_step': next_step.label}

        approval_request.status = 'approved'
        approval_request.completed_at = timezone.now()
        approval_request.save(update_fields=['status', 'completed_at'])
        return {'result': 'approved', 'step': step.label}


def approval_status_payload(obj):
    request = get_request_for_object(obj)
    if not request:
        return None

    step = _current_step(request)
    decisions = [
        {
            'step_order': d.step_order,
            'step_label': d.step_label,
            'decision': d.decision,
            'decided_by': d.decided_by.username if d.decided_by else None,
            'comment': d.comment,
            'decided_at': d.decided_at,
        }
        for d in request.decisions.order_by('step_order')
    ]
    return {
        'request_id': request.id,
        'status': request.status,
        'workflow': request.workflow.name,
        'current_step': step.label if step else None,
        'current_step_order': request.current_step_order,
        'decisions': decisions,
    }

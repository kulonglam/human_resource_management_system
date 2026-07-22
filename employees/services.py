"""Employee lifecycle use-cases (application layer)."""

from django.utils import timezone

from accounts.models import CustomUser


def assign_organization_if_needed(employee, user):
    """Attach creating user's organization when the employee has none."""
    org_id = getattr(user, 'organization_id', None)
    if org_id and not employee.organization_id:
        employee.organization_id = org_id
        employee.save(update_fields=['organization_id'])
    return employee


def after_employee_created(employee):
    """Side-effects after an employee record is created."""
    from events.services import publish_event
    from integrations.services import dispatch_webhook

    payload = {
        'id': employee.id,
        'email': employee.email,
        'full_name': employee.full_name,
        'department_id': employee.department_id,
        'job_title': employee.job_title,
    }
    publish_event('employee.created', payload)
    dispatch_webhook('employee.created', payload)
    return employee


def terminate_employee(employee, *, exit_reason, exit_notes='', actor=None):
    """
    Deactivate employee (and linked user if any), set exit fields, emit webhook.
    Does not write audit logs — the HTTP adapter remains responsible for audit.
    """
    from integrations.services import dispatch_webhook

    employee.is_active = False
    employee.termination_date = timezone.now().date()
    employee.exit_reason = exit_reason
    employee.exit_notes = exit_notes or ''
    employee.save()

    try:
        user = CustomUser.objects.get(email=employee.email)
        user.is_active = False
        user.save(update_fields=['is_active'])
    except CustomUser.DoesNotExist:
        pass

    payload = {
        'id': employee.id,
        'email': employee.email,
        'full_name': employee.full_name,
        'exit_reason': employee.exit_reason,
    }
    from events.services import publish_event
    publish_event('employee.terminated', payload)
    dispatch_webhook('employee.terminated', payload)
    return employee

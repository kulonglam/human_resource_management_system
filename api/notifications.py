import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(subject, message, recipient_list):
    recipients = [email for email in recipient_list if email]
    if not recipients:
        return False
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception('Failed to send email: %s', subject)
        return False


def notify_leave_submitted(leave):
    employee = leave.employee
    subject = f'[HRMIS] New leave request — {employee.full_name}'
    message = (
        f'A new leave request requires review.\n\n'
        f'Employee: {employee.full_name}\n'
        f'Type: {leave.get_leave_type_display()}\n'
        f'Dates: {leave.start_date} to {leave.end_date} ({leave.duration} days)\n'
        f'Reason: {leave.reason}\n'
    )
    recipients = []
    if settings.HR_NOTIFY_EMAIL:
        recipients.append(settings.HR_NOTIFY_EMAIL)
    if employee.department and employee.department.manager_contact:
        if '@' in employee.department.manager_contact:
            recipients.append(employee.department.manager_contact)
    return _send(subject, message, recipients)


def notify_leave_decision(leave, decision):
    employee = leave.employee
    if not employee.email:
        return False
    subject = f'[HRMIS] Leave request {decision}'
    message = (
        f'Hello {employee.full_name},\n\n'
        f'Your leave request has been {decision}.\n\n'
        f'Type: {leave.get_leave_type_display()}\n'
        f'Dates: {leave.start_date} to {leave.end_date}\n'
        f'Reviewed by: {leave.reviewed_by or "HR"}\n'
    )
    return _send(subject, message, [employee.email])

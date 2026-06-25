import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

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


def _render(template_name, context):
    return render_to_string(template_name, context).strip()


def _hr_recipients(employee=None):
    recipients = []
    if settings.HR_NOTIFY_EMAIL:
        recipients.append(settings.HR_NOTIFY_EMAIL)
    if employee and employee.department and employee.department.manager_contact:
        if '@' in employee.department.manager_contact:
            recipients.append(employee.department.manager_contact)
    return recipients


def notify_leave_submitted(leave):
    employee = leave.employee
    subject = f'[HRMIS] New leave request — {employee.full_name}'
    message = _render('emails/leave_submitted.txt', {
        'employee_name': employee.full_name,
        'leave_type': leave.get_leave_type_display(),
        'start_date': leave.start_date,
        'end_date': leave.end_date,
        'duration': leave.duration,
        'reason': leave.reason,
    })
    return _send(subject, message, _hr_recipients(employee))


def notify_leave_decision(leave, decision):
    employee = leave.employee
    if not employee.email:
        return False
    subject = f'[HRMIS] Leave request {decision}'
    message = _render('emails/leave_decision.txt', {
        'employee_name': employee.full_name,
        'decision': decision,
        'leave_type': leave.get_leave_type_display(),
        'start_date': leave.start_date,
        'end_date': leave.end_date,
        'reviewed_by': leave.reviewed_by or 'HR',
    })
    return _send(subject, message, [employee.email])


def notify_expense_submitted(expense):
    employee = expense.employee
    subject = f'[HRMIS] New expense claim — {employee.full_name}'
    message = _render('emails/expense_submitted.txt', {
        'employee_name': employee.full_name,
        'category': expense.category.name if expense.category else 'Uncategorized',
        'amount': expense.amount,
        'currency': 'KES',
        'description': expense.description,
        'expense_date': expense.expense_date,
    })
    return _send(subject, message, _hr_recipients(employee))


def notify_expense_decision(expense, decision):
    employee = expense.employee
    if not employee.email:
        return False
    subject = f'[HRMIS] Expense claim {decision}'
    message = _render('emails/expense_decision.txt', {
        'employee_name': employee.full_name,
        'decision': decision,
        'category': expense.category.name if expense.category else 'Uncategorized',
        'amount': expense.amount,
        'currency': 'KES',
        'description': expense.description,
        'rejection_reason': expense.rejection_reason if decision == 'rejected' else '',
        'reviewed_on': expense.approved_date or expense.updated_at,
    })
    return _send(subject, message, [employee.email])


def notify_appraisal_submitted(appraisal, submitted_by='HR'):
    employee = appraisal.employee
    subject = f'[HRMIS] Appraisal submitted — {employee.full_name}'
    message = _render('emails/appraisal_submitted.txt', {
        'employee_name': employee.full_name,
        'period_start': appraisal.appraisal_period_start,
        'period_end': appraisal.appraisal_period_end,
        'overall_rating': appraisal.overall_rating,
        'submitted_by': submitted_by,
    })
    recipients = _hr_recipients(employee)
    if employee.email:
        recipients.append(employee.email)
    return _send(subject, message, recipients)


def notify_appraisal_approved(appraisal):
    employee = appraisal.employee
    if not employee.email:
        return False
    subject = f'[HRMIS] Appraisal approved — {employee.full_name}'
    message = _render('emails/appraisal_approved.txt', {
        'employee_name': employee.full_name,
        'period_start': appraisal.appraisal_period_start,
        'period_end': appraisal.appraisal_period_end,
        'overall_rating': appraisal.overall_rating,
        'approved_at': appraisal.approved_at,
    })
    return _send(subject, message, [employee.email])


def notify_discipline_appeal_submitted(appeal):
    employee = appeal.discipline.employee
    subject = f'[HRMIS] Discipline appeal submitted — {employee.full_name}'
    message = _render('emails/discipline_appeal_submitted.txt', {
        'employee_name': employee.full_name,
        'discipline_type': appeal.discipline.get_discipline_type_display(),
        'appeal_date': appeal.appeal_date,
        'appeal_reason': appeal.appeal_reason,
    })
    return _send(subject, message, _hr_recipients(employee))


def notify_discipline_appeal_decision(appeal, decision):
    employee = appeal.discipline.employee
    if not employee.email:
        return False
    subject = f'[HRMIS] Discipline appeal {decision}'
    message = _render('emails/discipline_appeal_decision.txt', {
        'employee_name': employee.full_name,
        'decision': decision,
        'discipline_type': appeal.discipline.get_discipline_type_display(),
        'review_date': appeal.review_date or appeal.created_at.date(),
        'review_notes': appeal.review_notes,
    })
    return _send(subject, message, [employee.email])


def notify_application_status(application, previous_status):
    if not application.email:
        return False
    subject = f'[HRMIS] Application update — {application.job.title}'
    message = _render('emails/application_status.txt', {
        'applicant_name': f'{application.first_name} {application.last_name}',
        'job_title': application.job.title,
        'previous_status': previous_status,
        'new_status': application.get_status_display(),
    })
    return _send(subject, message, [application.email])


def notify_benefit_enrollment_submitted(enrollment):
    employee = enrollment.employee
    subject = f'[HRMIS] Benefit enrollment request — {employee.full_name}'
    message = _render('emails/benefit_enrollment_submitted.txt', {
        'employee_name': employee.full_name,
        'benefit_name': enrollment.benefit.name,
        'enrollment_date': enrollment.enrollment_date,
        'plan_type': enrollment.plan_type or 'Standard',
    })
    return _send(subject, message, _hr_recipients(employee))


def notify_benefit_enrollment_decision(enrollment, decision):
    employee = enrollment.employee
    if not employee.email:
        return False
    subject = f'[HRMIS] Benefit enrollment {decision}'
    message = _render('emails/benefit_enrollment_decision.txt', {
        'employee_name': employee.full_name,
        'decision': decision,
        'benefit_name': enrollment.benefit.name,
        'enrollment_date': enrollment.enrollment_date,
        'plan_type': enrollment.plan_type or 'Standard',
        'status': enrollment.get_status_display(),
    })
    return _send(subject, message, [employee.email])

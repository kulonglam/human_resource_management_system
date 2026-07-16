"""Generate and email scheduled reports."""

import io
import logging
from datetime import timedelta

from django.core.mail import EmailMessage
from django.utils import timezone

from reports.models import ScheduledReport

logger = logging.getLogger(__name__)


def _build_report_payload(scheduled):
    from rest_framework.test import APIRequestFactory

    from api.report_views import (
        AttendanceReportView,
        LeaveReportView,
        PayrollReportView,
        PerformanceReportView,
        RecruitmentReportView,
    )

    factory = APIRequestFactory()
    params = scheduled.filters or {}
    request = factory.get('/reports/', params)
    request.user = scheduled.created_by

    mapping = {
        'attendance': AttendanceReportView,
        'leave': LeaveReportView,
        'payroll': PayrollReportView,
        'performance': PerformanceReportView,
        'recruitment': RecruitmentReportView,
    }
    view = mapping.get(scheduled.report_type)
    if not view:
        raise ValueError(f'Unsupported report type: {scheduled.report_type}')
    response = view.as_view()(request)
    return response.data


def _export_attachment(scheduled, data):
    from api.report_exports import export_rows_csv, export_rows_pdf, export_rows_xlsx

    rows = data.get('rows') or data.get('records') or []
    if scheduled.report_type == 'payroll':
        columns = [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'gross_salary', 'label': 'Gross (UGX)'},
            {'key': 'tax', 'label': 'PAYE (UGX)'},
            {'key': 'net_salary', 'label': 'Net (UGX)'},
        ]
    elif scheduled.report_type == 'attendance':
        columns = [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'date', 'label': 'Date'},
            {'key': 'status', 'label': 'Status'},
        ]
    else:
        columns = [{'key': k, 'label': k.replace('_', ' ').title()} for k in (rows[0] or {}).keys()]

    if scheduled.export_format == 'pdf':
        response = export_rows_pdf(rows, columns, scheduled.name, scheduled.name)
    elif scheduled.export_format == 'csv':
        response = export_rows_csv(rows, columns, scheduled.name)
    else:
        response = export_rows_xlsx(rows, columns, scheduled.name, scheduled.name)

    filename = response['Content-Disposition'].split('filename=')[-1].strip('"')
    content_type = response['Content-Type']
    return filename, content_type, response.content


def deliver_scheduled_report(scheduled_id):
    scheduled = ScheduledReport.objects.select_related('created_by').get(pk=scheduled_id)
    if not scheduled.is_active:
        return {'status': 'skipped', 'reason': 'inactive'}

    recipients = [email for email in scheduled.recipient_emails if email]
    if not recipients:
        return {'status': 'skipped', 'reason': 'no recipients'}

    data = _build_report_payload(scheduled)
    filename, content_type, content = _export_attachment(scheduled, data)

    email = EmailMessage(
        subject=f'[HRMIS] Scheduled report: {scheduled.name}',
        body=(
            f'Attached is the {scheduled.get_report_type_display()} '
            f'({scheduled.get_frequency_display().lower()}) generated on '
            f'{timezone.now().strftime("%d %b %Y %H:%M")} (Africa/Kampala).'
        ),
        from_email=None,
        to=recipients,
    )
    email.attach(filename, content, content_type)
    email.send(fail_silently=False)

    scheduled.last_run_at = timezone.now()
    scheduled.save(update_fields=['last_run_at', 'updated_at'])
    return {'status': 'sent', 'recipients': len(recipients), 'filename': filename}


def run_due_scheduled_reports():
    now = timezone.now()
    due = []
    for scheduled in ScheduledReport.objects.filter(is_active=True):
        if not scheduled.last_run_at:
            due.append(scheduled.id)
            continue
        delta = now - scheduled.last_run_at
        if scheduled.frequency == 'daily' and delta >= timedelta(days=1):
            due.append(scheduled.id)
        elif scheduled.frequency == 'weekly' and delta >= timedelta(days=7):
            due.append(scheduled.id)
        elif scheduled.frequency == 'monthly' and delta >= timedelta(days=28):
            due.append(scheduled.id)

    results = []
    for scheduled_id in due:
        try:
            results.append({'id': scheduled_id, **deliver_scheduled_report(scheduled_id)})
        except Exception as exc:
            logger.exception('Scheduled report %s failed', scheduled_id)
            results.append({'id': scheduled_id, 'status': 'error', 'detail': str(exc)})
    return {'processed': len(results), 'results': results}

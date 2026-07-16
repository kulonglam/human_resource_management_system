"""Background tasks for reports and maintenance."""

import logging

logger = logging.getLogger(__name__)


def task_deliver_scheduled_report(scheduled_id):
    from reports.services import deliver_scheduled_report
    return deliver_scheduled_report(scheduled_id)


def task_run_due_scheduled_reports():
    from reports.services import run_due_scheduled_reports
    return run_due_scheduled_reports()


def task_run_scheduled_maintenance():
    from django.core.management import call_command
    call_command('run_scheduled_tasks', skip_backup=True)

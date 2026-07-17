import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run scheduled HR tasks: leave accrual, document reminders, optional backup.'

    def add_arguments(self, parser):
        parser.add_argument('--skip-backup', action='store_true')
        parser.add_argument(
            '--skip-retention',
            action='store_true',
            help='Skip data retention policy enforcement.',
        )
        parser.add_argument(
            '--verify-backup',
            action='store_true',
            help='After backup, run verify_backup on the newest file.',
        )
        parser.add_argument('--carry-forward', action='store_true')

    def handle(self, *args, **options):
        results = {}

        try:
            from leaves.services import accrue_monthly_balances, carry_forward_balances

            results['leave_accrual'] = accrue_monthly_balances()
            if options['carry_forward']:
                results['carry_forward'] = carry_forward_balances(
                    results['leave_accrual']['year'] - 1,
                    results['leave_accrual']['year'],
                )
        except Exception as exc:
            results['leave_accrual'] = str(exc)

        try:
            from attendance.services import document_expiry_reminders
            results['document_reminders'] = document_expiry_reminders()
        except Exception as exc:
            results['document_reminders'] = str(exc)

        if not options['skip_backup']:
            try:
                from django.core.management import call_command
                call_command('backup_database')
                results['backup'] = 'ok'
                if options['verify_backup']:
                    call_command('verify_backup')
                    results['backup_verify'] = 'ok'
            except Exception as exc:
                results['backup'] = str(exc)

        if not options['skip_retention']:
            try:
                from django.core.management import call_command
                call_command('apply_retention_policies')
                results['retention'] = 'ok'
            except Exception as exc:
                results['retention'] = str(exc)

        try:
            from reports.services import run_due_scheduled_reports
            results['scheduled_reports'] = run_due_scheduled_reports()
        except Exception as exc:
            results['scheduled_reports'] = str(exc)

        try:
            from api.ops_monitoring import emit_ops_alerts

            results['ops_alerts'] = emit_ops_alerts()
        except Exception as exc:
            results['ops_alerts'] = str(exc)

        self.stdout.write(self.style.SUCCESS(f'Scheduled tasks finished: {results}'))

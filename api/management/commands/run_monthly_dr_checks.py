"""Monthly disaster-recovery workflow for staging or manual ops runs."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create backup, verify it, and run an isolated restore drill with evidence recording.'

    def handle(self, *args, **options):
        call_command('backup_database')
        call_command('verify_backup')
        result = call_command('run_restore_drill', record_evidence=True)
        self.stdout.write(self.style.SUCCESS(f'Monthly DR checks finished: {result}'))

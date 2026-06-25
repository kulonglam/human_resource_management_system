from django.core.management.base import BaseCommand

from compliance.retention import apply_all_retention_policies


class Command(BaseCommand):
    help = 'Purge records older than configured data retention policies.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report how many records would be deleted without deleting.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        results = apply_all_retention_policies(dry_run=dry_run)
        if not results:
            self.stdout.write('No active retention policies found.')
            return

        prefix = 'Would purge' if dry_run else 'Purged'
        for item in results:
            self.stdout.write(f'{prefix} {item["purged"]} {item["category"]} record(s)')

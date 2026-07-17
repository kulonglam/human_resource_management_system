"""Prune local database backups per BACKUP_RETENTION_COUNT / BACKUP_RETENTION_DAYS."""

from django.core.management.base import BaseCommand

from api.backup_storage import prune_local_backups


class Command(BaseCommand):
    help = 'Delete old local backups according to retention settings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-count',
            type=int,
            default=None,
            help='Override BACKUP_RETENTION_COUNT (newest N to keep).',
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=None,
            help='Override BACKUP_RETENTION_DAYS (delete older than D days).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List files that would be deleted without deleting.',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            from pathlib import Path
            import time
            from django.conf import settings
            from api.backup_storage import list_backup_files

            keep_count = options['keep_count']
            if keep_count is None:
                keep_count = int(getattr(settings, 'BACKUP_RETENTION_COUNT', 14) or 0)
            keep_days = options['keep_days']
            if keep_days is None:
                keep_days = int(getattr(settings, 'BACKUP_RETENTION_DAYS', 30) or 0)

            files = list_backup_files()
            would = set()
            if keep_count > 0 and len(files) > keep_count:
                would.update(files[keep_count:])
            if keep_days > 0:
                cutoff = time.time() - (keep_days * 86400)
                would.update(p for p in files if p.stat().st_mtime < cutoff)
            if not would:
                self.stdout.write('No backups would be pruned.')
                return
            for path in sorted(would, key=lambda p: p.stat().st_mtime):
                self.stdout.write(f'Would delete: {path.name}')
            self.stdout.write(self.style.WARNING(f'Dry run: {len(would)} file(s)'))
            return

        kwargs = {}
        if options['keep_count'] is not None:
            kwargs['keep_count'] = options['keep_count']
        if options['keep_days'] is not None:
            kwargs['keep_days'] = options['keep_days']
        deleted = prune_local_backups(**kwargs)
        if deleted:
            self.stdout.write(self.style.SUCCESS(f'Pruned {len(deleted)} backup(s): {", ".join(deleted)}'))
        else:
            self.stdout.write('No backups pruned.')

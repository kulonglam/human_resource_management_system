from django.core.management.base import BaseCommand

from events.services import drain_outbox


class Command(BaseCommand):
    help = 'Drain pending domain events from the transactional outbox.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        result = drain_outbox(limit=options['limit'])
        self.stdout.write(self.style.SUCCESS(f'Outbox drain: {result}'))

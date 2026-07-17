from django.core.management.base import BaseCommand

from api.ops_monitoring import emit_ops_alerts


class Command(BaseCommand):
    help = 'Check health/SLO state and emit admin alerts for degradations.'

    def handle(self, *args, **options):
        result = emit_ops_alerts()
        self.stdout.write(self.style.SUCCESS(f'Ops alert check finished: {result}'))

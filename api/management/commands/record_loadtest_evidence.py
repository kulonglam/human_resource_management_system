"""Record Locust / soak results into the compliance evidence pack."""

from django.core.management.base import BaseCommand

from api.assurance import update_loadtest_evidence_pack


class Command(BaseCommand):
    help = 'Update the Availability/SLO evidence pack with load or soak test results.'

    def add_arguments(self, parser):
        parser.add_argument('--requests', type=int, default=0)
        parser.add_argument('--error-rate', type=float, default=0.0)
        parser.add_argument('--median-ms', type=float, default=0.0)
        parser.add_argument('--p95-ms', type=float, default=0.0)
        parser.add_argument('--notes', type=str, default='')
        parser.add_argument('--url', type=str, default='', dest='evidence_url')
        parser.add_argument(
            '--ok',
            action='store_true',
            help='Mark evidence ready (pass). Without this, status is gap unless auto-derived.',
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Derive pass/fail from error-rate ≤ 0.005 and p95 ≤ 1500.',
        )

    def handle(self, *args, **options):
        ok = bool(options['ok'])
        if options['auto']:
            ok = options['error_rate'] <= 0.005 and options['p95_ms'] <= 1500
        pack = update_loadtest_evidence_pack(
            ok=ok,
            requests=options['requests'],
            error_rate=options['error_rate'],
            median_ms=options['median_ms'],
            p95_ms=options['p95_ms'],
            notes=options['notes'],
            evidence_url=options['evidence_url'],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Evidence pack '{pack.title}' status={pack.status} (control={pack.control})"
            )
        )

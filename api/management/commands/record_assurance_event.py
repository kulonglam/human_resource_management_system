"""Record a security/compliance assurance activity into an evidence pack."""

from django.core.management.base import BaseCommand, CommandError

from api.assurance import record_assurance_event
from compliance.models import ComplianceEvidencePack


class Command(BaseCommand):
    help = (
        'Mark a compliance evidence pack ready/gap after pen-test, access review, '
        'or other assurance work.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--control',
            required=True,
            choices=[c[0] for c in ComplianceEvidencePack.CONTROL_CHOICES],
        )
        parser.add_argument('--title', required=True)
        parser.add_argument('--description', default='')
        parser.add_argument('--url', default='', dest='evidence_url')
        parser.add_argument('--owner', default='Security')
        parser.add_argument('--review-days', type=int, default=90)
        parser.add_argument('--ok', action='store_true', help='Mark status ready')
        parser.add_argument('--gap', action='store_true', help='Mark status gap')

    def handle(self, *args, **options):
        if options['ok'] == options['gap']:
            raise CommandError('Specify exactly one of --ok or --gap')
        pack = record_assurance_event(
            control=options['control'],
            title=options['title'],
            ok=bool(options['ok']),
            description=options['description'],
            evidence_url=options['evidence_url'],
            owner=options['owner'],
            review_days=options['review_days'],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Evidence pack '{pack.title}' status={pack.status} (control={pack.control})"
            )
        )

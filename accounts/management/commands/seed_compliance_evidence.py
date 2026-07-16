from django.core.management.base import BaseCommand

from compliance.models import ComplianceEvidencePack


DEFAULT_EVIDENCE = [
    ('access_control', 'RBAC role permissions matrix', 'ready', 'HR Admin'),
    ('encryption', 'Encrypted employee PII fields', 'ready', 'Security'),
    ('backup_restore', 'Database backup and restore runbook', 'ready', 'Ops'),
    ('audit_logging', 'Sensitive data access and audit logs', 'ready', 'Security'),
    ('data_retention', 'Retention policies and purge jobs', 'ready', 'Compliance'),
    ('vulnerability_mgmt', 'Vulnerability finding SLA tracker', 'draft', 'Security'),
    ('incident_response', 'Payroll-day and leave-spike runbooks', 'ready', 'Ops'),
]


class Command(BaseCommand):
    help = 'Seed default compliance evidence pack entries.'

    def handle(self, *args, **options):
        created = 0
        for control, title, status, owner in DEFAULT_EVIDENCE:
            _, was_created = ComplianceEvidencePack.objects.get_or_create(
                control=control,
                title=title,
                defaults={'status': status, 'owner': owner, 'description': title},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Evidence packs ready ({created} created).'))

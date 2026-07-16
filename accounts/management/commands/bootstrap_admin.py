import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import CustomUser, Role


class Command(BaseCommand):
    help = 'Create the initial production administrator without modifying existing users.'

    @transaction.atomic
    def handle(self, *args, **options):
        username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME', 'admin')
        email = os.environ.get('BOOTSTRAP_ADMIN_EMAIL', 'admin@hrmis.local')
        password = os.environ.get('SEED_ADMIN_PASSWORD', '')

        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write(f'Administrator "{username}" already exists; no changes made.')
            return
        if not password:
            raise CommandError(
                'SEED_ADMIN_PASSWORD is required when creating the initial administrator.',
            )

        role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=role,
        )
        self.stdout.write(self.style.SUCCESS(f'Created administrator "{username}".'))

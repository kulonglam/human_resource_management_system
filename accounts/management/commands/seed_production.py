"""One-shot production bootstrap: roles, admin, workflows, document access, holidays."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from accounts.models import CustomUser, Role


def _env_flag(name):
    return os.environ.get(name, '').lower() in ('1', 'true', 'yes')


def reset_admin_password():
    """Set the bootstrap admin password from SEED_ADMIN_PASSWORD."""
    username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME', 'admin')
    password = os.environ.get('SEED_ADMIN_PASSWORD', '')
    if not password:
        raise CommandError('SEED_ADMIN_PASSWORD is required to reset the admin password.')
    user = CustomUser.objects.filter(username=username).first()
    if not user:
        return False
    user.set_password(password)
    user.save(update_fields=['password'])
    return True


class Command(BaseCommand):
    help = (
        'Idempotent production bootstrap: roles, admin, workflows, document access, '
        'and public holidays. Optional demo users via --with-users or SEED_PRODUCTION_WITH_USERS.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Required when DATABASE_URL is set (hosted Postgres / production).',
        )
        parser.add_argument(
            '--with-users',
            action='store_true',
            help='Also seed manager/employee login users and sample HR records (seed_data).',
        )
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset seed user passwords when --with-users runs (requires SEED_*_PASSWORD on hosted DB).',
        )
        parser.add_argument(
            '--compliance',
            action='store_true',
            help='Seed default compliance evidence packs.',
        )
        parser.add_argument(
            '--skip-holidays',
            action='store_true',
            help='Do not seed Uganda public holidays for the current year.',
        )

    def handle(self, *args, **options):
        hosted = bool(os.environ.get('DATABASE_URL'))
        if hosted and not options['confirm']:
            raise CommandError(
                'Refusing to seed a hosted database without --confirm. '
                'Set SEED_ADMIN_PASSWORD (and SEED_MANAGER_PASSWORD / SEED_EMPLOYEE_PASSWORD '
                'if using --with-users) before running.'
            )

        with_users = options['with_users'] or _env_flag('SEED_PRODUCTION_WITH_USERS')
        reset_passwords = options['reset_passwords'] or _env_flag('SEED_RESET_PASSWORDS')

        for role_name in (Role.ADMIN, Role.MANAGER, Role.EMPLOYEE):
            Role.objects.get_or_create(name=role_name)

        call_command('bootstrap_admin')
        if reset_passwords and reset_admin_password():
            self.stdout.write(self.style.SUCCESS('Admin password reset from SEED_ADMIN_PASSWORD.'))
        call_command('seed_workflows')
        call_command('seed_document_access')

        if not options['skip_holidays']:
            try:
                call_command('seed_uganda_holidays')
            except Exception as exc:  # pragma: no cover - optional calendar data
                self.stdout.write(self.style.WARNING(f'Holidays seed skipped: {exc}'))

        if options['compliance']:
            call_command('seed_compliance_evidence')

        if with_users:
            call_command('seed_data', reset_password=reset_passwords)

        self.stdout.write(self.style.SUCCESS('Production seed complete.'))
        if hosted:
            self.stdout.write(
                '  Admin login: use BOOTSTRAP_ADMIN_USERNAME (default admin) and SEED_ADMIN_PASSWORD.'
            )
        if with_users:
            self.stdout.write(
                '  Demo users seeded (manager, employee). Passwords from SEED_*_PASSWORD env vars.'
            )

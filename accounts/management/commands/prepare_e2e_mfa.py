"""Enable a fixed TOTP secret on a seed user for Playwright MFA E2E tests."""

from django.core.management.base import BaseCommand, CommandError

from accounts.models import CustomUser

# Base32 secret for deterministic E2E TOTP codes (otplib / pyotp compatible).
E2E_MFA_SECRET = 'E2ETESTMFASECRETKEY000000'


class Command(BaseCommand):
    help = 'Enable MFA on a seed user with a fixed secret for E2E login tests.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--secret', default=E2E_MFA_SECRET)
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Clear MFA on the user (restores default E2E login).',
        )

    def handle(self, *args, **options):
        try:
            user = CustomUser.objects.get(username=options['username'])
        except CustomUser.DoesNotExist as exc:
            raise CommandError(f"User {options['username']!r} not found. Run seed_data first.") from exc

        if options['disable']:
            user.mfa_secret = ''
            user.mfa_enabled = False
            user.save(update_fields=['mfa_secret', 'mfa_enabled'])
            self.stdout.write(self.style.SUCCESS(f'MFA disabled for {user.username}.'))
            return

        user.mfa_secret = options['secret']
        user.mfa_enabled = True
        user.save(update_fields=['mfa_secret', 'mfa_enabled'])
        self.stdout.write(self.style.SUCCESS(
            f'MFA enabled for {user.username} (fixed E2E secret).',
        ))

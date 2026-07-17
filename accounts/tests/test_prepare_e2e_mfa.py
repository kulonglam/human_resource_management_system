"""Tests for E2E MFA preparation command."""

from django.core.management import call_command
from django.test import TestCase

from accounts.management.commands.prepare_e2e_mfa import E2E_MFA_SECRET
from accounts.models import CustomUser, Role


class PrepareE2eMfaCommandTests(TestCase):
    def setUp(self):
        role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        self.admin = CustomUser.objects.create_user(
            username='mfa-e2e-admin',
            email='mfa-e2e@test.local',
            password='Pass123!',
            role=role,
        )

    def test_enable_and_disable_fixed_secret(self):
        call_command('prepare_e2e_mfa', username='mfa-e2e-admin')
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.mfa_enabled)
        self.assertEqual(self.admin.mfa_secret, E2E_MFA_SECRET)

        call_command('prepare_e2e_mfa', username='mfa-e2e-admin', disable=True)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.mfa_enabled)
        self.assertEqual(self.admin.mfa_secret, '')

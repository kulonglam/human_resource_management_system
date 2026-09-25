from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounts.models import CustomUser, Role
from attendance.models import PublicHoliday
from documents.models import DocumentAccessRule
from workflows.models import ApprovalWorkflow


class SeedProductionCommandTests(TestCase):
    @patch.dict('os.environ', {'DATABASE_URL': 'postgres://localhost/test'}, clear=False)
    def test_requires_confirm_on_hosted_database(self):
        with self.assertRaises(CommandError) as ctx:
            call_command('seed_production')
        self.assertIn('--confirm', str(ctx.exception))

    @patch.dict(
        'os.environ',
        {
            'SEED_ADMIN_PASSWORD': 'ProdAdminPass123!',
            'DATABASE_URL': '',
        },
        clear=True,
    )
    def test_seeds_core_production_data(self):
        call_command('seed_production')

        self.assertEqual(
            set(Role.objects.values_list('name', flat=True)),
            {Role.ADMIN, Role.MANAGER, Role.EMPLOYEE},
        )
        self.assertTrue(CustomUser.objects.filter(username='admin', is_superuser=True).exists())
        self.assertTrue(ApprovalWorkflow.objects.filter(workflow_type='leave', is_default=True).exists())
        self.assertTrue(DocumentAccessRule.objects.filter(role__name=Role.ADMIN).exists())
        self.assertTrue(PublicHoliday.objects.filter(name="New Year's Day").exists())

    @patch.dict(
        'os.environ',
        {
            'SEED_ADMIN_PASSWORD': 'ProdAdminPass123!',
            'SEED_MANAGER_PASSWORD': 'ProdManagerPass123!',
            'SEED_EMPLOYEE_PASSWORD': 'ProdEmployeePass123!',
            'DATABASE_URL': '',
        },
        clear=True,
    )
    def test_with_users_seeds_demo_accounts(self):
        call_command('seed_production', with_users=True)

        self.assertTrue(CustomUser.objects.filter(username='manager').exists())
        self.assertTrue(CustomUser.objects.filter(username='employee').exists())

    @patch.dict(
        'os.environ',
        {
            'SEED_ADMIN_PASSWORD': 'ProdAdminPass123!',
            'SEED_PRODUCTION_WITH_USERS': '1',
            'DATABASE_URL': 'postgres://localhost/test',
        },
        clear=False,
    )
    @patch('accounts.management.commands.seed_production.call_command')
    def test_env_with_users_flag(self, mock_call_command):
        call_command('seed_production', confirm=True)
        called = [args[0] for args, _kwargs in mock_call_command.call_args_list]
        self.assertIn('seed_data', called)

    @patch.dict(
        'os.environ',
        {
            'SEED_ADMIN_PASSWORD': 'NewAdminPass123!',
            'SEED_RESET_PASSWORDS': '1',
            'DATABASE_URL': '',
        },
        clear=True,
    )
    def test_env_reset_updates_existing_admin_password(self):
        call_command('seed_production')
        admin = CustomUser.objects.get(username='admin')
        admin.set_password('OldAdminPass123!')
        admin.save(update_fields=['password'])

        call_command('seed_production')
        admin.refresh_from_db()
        self.assertTrue(admin.check_password('NewAdminPass123!'))

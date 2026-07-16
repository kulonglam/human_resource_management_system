from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from accounts.models import CustomUser, Role


class BootstrapAdminCommandTests(TestCase):
    @patch.dict(
        'os.environ',
        {
            'BOOTSTRAP_ADMIN_USERNAME': 'initial-admin',
            'BOOTSTRAP_ADMIN_EMAIL': 'initial-admin@test.local',
            'SEED_ADMIN_PASSWORD': 'InitialAdminPass123!',
        },
    )
    def test_creates_initial_admin_once_without_resetting_password(self):
        call_command('bootstrap_admin')
        user = CustomUser.objects.get(username='initial-admin')

        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role.name, Role.ADMIN)
        self.assertTrue(user.check_password('InitialAdminPass123!'))

        user.set_password('ChangedAfterFirstLogin123!')
        user.save(update_fields=['password'])
        call_command('bootstrap_admin')
        user.refresh_from_db()

        self.assertTrue(user.check_password('ChangedAfterFirstLogin123!'))

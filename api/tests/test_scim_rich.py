"""Rich SCIM Users/Groups coverage."""

from accounts.models import CustomUser, Role

from .base import HRAPITestCase


class RichScimTests(HRAPITestCase):
    def setUp(self):
        super().setUp()
        self.login('admin', 'AdminPass123!')

    def test_service_provider_config(self):
        response = self.client.get('/api/v1/scim/v2/ServiceProviderConfig')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['filter']['supported'])
        self.assertTrue(response.data['patch']['supported'])

    def test_groups_list_maps_roles(self):
        response = self.client.get('/api/v1/scim/v2/Groups')
        self.assertEqual(response.status_code, 200)
        names = {g['displayName'] for g in response.data['Resources']}
        self.assertIn(Role.ADMIN, names)

    def test_user_patch_deactivates(self):
        user = CustomUser.objects.create_user(
            username='scim-target', email='scim-target@test.local',
            password='Pass123!', role=self.employee_role,
        )
        response = self.client.patch(
            f'/api/v1/scim/v2/Users/{user.id}',
            {
                'schemas': ['urn:ietf:params:scim:api:messages:2.0:PatchOp'],
                'Operations': [{'op': 'replace', 'path': 'active', 'value': False}],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_filter_by_username(self):
        response = self.client.get(
            '/api/v1/scim/v2/Users',
            {'filter': 'userName eq "admin"'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['totalResults'], 1)
        self.assertEqual(response.data['Resources'][0]['userName'], 'admin')

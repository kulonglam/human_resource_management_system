"""Organization (tenant) isolation tests.

Verifies that org-scoped users cannot read data belonging to another
organization, and that single-tenant deployments (no organization set)
keep full visibility.
"""
import datetime

from accounts.models import CustomUser, Organization
from departments.models import Department
from employees.models import Employee
from leaves.models import Leave

from .base import HRAPITestCase


class OrganizationScopingTests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.org_a = Organization.objects.create(name='Org A', slug='org-a')
        cls.org_b = Organization.objects.create(name='Org B', slug='org-b')

        cls.admin_a = CustomUser.objects.create_user(
            username='admin_a',
            email='admin_a@test.local',
            password='AdminPass123!',
            role=cls.admin_role,
            organization=cls.org_a,
        )

        cls.dept_a = Department.objects.create(
            name='Org A Dept', location='A', organization=cls.org_a,
        )
        cls.dept_b = Department.objects.create(
            name='Org B Dept', location='B', organization=cls.org_b,
        )

        cls.emp_a = Employee.objects.create(
            first_name='Alice', last_name='OrgA',
            date_of_birth='1990-01-01', gender='Female',
            email='alice@orga.local', mobile='0700000001',
            address='A', emergency_contact='0711111112',
            job_title='Engineer', department=cls.dept_a,
            date_joined='2024-01-01', account_number='111',
            bank='Bank', salary=1000, organization=cls.org_a,
        )
        cls.emp_b = Employee.objects.create(
            first_name='Bob', last_name='OrgB',
            date_of_birth='1990-01-01', gender='Male',
            email='bob@orgb.local', mobile='0700000002',
            address='B', emergency_contact='0711111113',
            job_title='Engineer', department=cls.dept_b,
            date_joined='2024-01-01', account_number='222',
            bank='Bank', salary=1000, organization=cls.org_b,
        )
        cls.leave_a = Leave.objects.create(
            employee=cls.emp_a, leave_type='annual',
            start_date=datetime.date(2026, 8, 3),
            end_date=datetime.date(2026, 8, 4),
            reason='Org A leave',
        )
        cls.leave_b = Leave.objects.create(
            employee=cls.emp_b, leave_type='annual',
            start_date=datetime.date(2026, 8, 3),
            end_date=datetime.date(2026, 8, 4),
            reason='Org B leave',
        )

    def _login(self, username, password):
        response = self.login(username, password)
        self.assertEqual(response.status_code, 200, response.content)

    def _results(self, payload):
        if isinstance(payload, dict) and 'results' in payload:
            return payload['results']
        return payload

    def test_org_admin_sees_only_own_org_employees(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get('/api/v1/employees/')
        self.assertEqual(response.status_code, 200)
        emails = {e['email'] for e in self._results(response.json())}
        self.assertIn('alice@orga.local', emails)
        self.assertNotIn('bob@orgb.local', emails)

    def test_org_admin_cannot_retrieve_other_org_employee(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get(f'/api/v1/employees/{self.emp_b.id}/')
        self.assertIn(response.status_code, (403, 404))

    def test_org_admin_sees_only_own_org_leaves(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get('/api/v1/leaves/')
        self.assertEqual(response.status_code, 200)
        ids = {l['id'] for l in self._results(response.json())}
        self.assertIn(self.leave_a.id, ids)
        self.assertNotIn(self.leave_b.id, ids)

    def test_org_admin_cannot_approve_other_org_leave(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.post(f'/api/v1/leaves/{self.leave_b.id}/approve/')
        self.assertIn(response.status_code, (403, 404))

    def test_global_admin_sees_all_orgs(self):
        """Admin without an organization keeps full (single-tenant) visibility."""
        self._login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/employees/')
        self.assertEqual(response.status_code, 200)
        emails = {e['email'] for e in self._results(response.json())}
        self.assertIn('alice@orga.local', emails)
        self.assertIn('bob@orgb.local', emails)

        response = self.client.get('/api/v1/leaves/')
        ids = {l['id'] for l in self._results(response.json())}
        self.assertIn(self.leave_a.id, ids)
        self.assertIn(self.leave_b.id, ids)

    def test_employee_created_by_org_admin_gets_org_assigned(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.post('/api/v1/employees/', {
            'first_name': 'New', 'last_name': 'Hire',
            'date_of_birth': '1995-05-05', 'gender': 'Female',
            'email': 'newhire@orga.local', 'mobile': '0700000003',
            'address': 'A', 'emergency_contact': '0711111114',
            'job_title': 'Analyst', 'department': self.dept_a.id,
            'date_joined': '2026-01-01', 'account_number': '333',
            'bank': 'Bank', 'salary': 900,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        employee = Employee.objects.get(email='newhire@orga.local')
        self.assertEqual(employee.organization_id, self.org_a.id)

    def test_org_admin_user_list_is_scoped(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, 200)
        usernames = {u['username'] for u in self._results(response.json())}
        # Own org + unscoped (system) users are visible.
        self.assertIn('admin_a', usernames)
        # Create an org B user and verify it is hidden.
        CustomUser.objects.create_user(
            username='admin_b', email='admin_b@test.local',
            password='AdminPass123!', role=self.admin_role,
            organization=self.org_b,
        )
        response = self.client.get('/api/v1/users/')
        usernames = {u['username'] for u in self._results(response.json())}
        self.assertNotIn('admin_b', usernames)

    def test_org_admin_sees_only_own_departments(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get('/api/v1/departments/')
        self.assertEqual(response.status_code, 200)
        names = {d['name'] for d in self._results(response.json())}
        self.assertIn('Org A Dept', names)
        self.assertNotIn('Org B Dept', names)

    def test_org_admin_job_postings_scoped(self):
        from recruitment.models import JobPosting

        job_a = JobPosting.objects.create(
            title='Role A', department='Eng', description='d', requirements='r',
            deadline=datetime.date(2026, 12, 1), organization=self.org_a,
        )
        JobPosting.objects.create(
            title='Role B', department='Eng', description='d', requirements='r',
            deadline=datetime.date(2026, 12, 1), organization=self.org_b,
        )
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get('/api/v1/jobs/')
        self.assertEqual(response.status_code, 200)
        titles = {j['title'] for j in self._results(response.json())}
        self.assertIn(job_a.title, titles)
        self.assertNotIn('Role B', titles)

    def test_org_admin_payroll_runs_scoped(self):
        from payroll.models import PayrollRun

        run_a = PayrollRun.objects.create(
            month=1, year=2026, organization=self.org_a, created_by=self.admin_a,
        )
        PayrollRun.objects.create(
            month=1, year=2026, organization=self.org_b, created_by=self.admin_user,
        )
        self._login('admin_a', 'AdminPass123!')
        response = self.client.get('/api/v1/payroll-runs/')
        self.assertEqual(response.status_code, 200)
        ids = {r['id'] for r in self._results(response.json())}
        self.assertIn(run_a.id, ids)
        self.assertEqual(len(ids), 1)

    def test_department_create_stamps_organization(self):
        self._login('admin_a', 'AdminPass123!')
        response = self.client.post('/api/v1/departments/', {
            'name': 'New Org A Dept', 'location': 'HQ',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        dept = Department.objects.get(name='New Org A Dept')
        self.assertEqual(dept.organization_id, self.org_a.id)

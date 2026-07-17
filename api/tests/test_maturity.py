from datetime import date, timedelta

from accounts.models import Organization
from compliance.models import ComplianceEvidencePack, VulnerabilityFinding
from payroll.models import Salary

from .base import HRAPITestCase


class MaturityAPITests(HRAPITestCase):
    def test_api_changelog_is_public(self):
        response = self.client.get('/api/v1/api-changelog/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['current_version'], '1.2.0')
        self.assertTrue(response['X-API-Version'])

    def test_health_includes_request_id(self):
        response = self.client.get('/api/v1/health/', HTTP_X_REQUEST_ID='test-req-1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Request-ID'], 'test-req-1')

    def test_deprecation_headers_on_analytics(self):
        self.login('manager', 'ManagerPass123!')
        response = self.client.get('/api/v1/reports/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Deprecation'], 'true')
        self.assertIn('Sunset', response)

    def test_admin_ops_and_slos(self):
        self.login('admin', 'AdminPass123!')
        ops = self.client.get('/api/v1/ops/status/')
        self.assertEqual(ops.status_code, 200)
        self.assertIn('disaster_recovery', ops.data)
        self.assertIn('infrastructure', ops.data)
        self.assertIn('alerts', ops.data)
        self.assertIn('active', ops.data['alerts'])
        self.assertIn('recent', ops.data['alerts'])
        self.assertIn('cooldowns', ops.data['alerts'])
        self.assertEqual(self.client.get('/api/v1/ops/slos/').status_code, 200)

    def test_organization_crud_and_scim_list(self):
        self.login('admin', 'AdminPass123!')
        create = self.client.post(
            '/api/v1/organizations/',
            {'name': 'Acme Uganda', 'slug': 'acme-ug', 'is_active': True},
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        self.assertTrue(Organization.objects.filter(slug='acme-ug').exists())

        scim = self.client.get('/api/v1/scim/v2/Users')
        self.assertEqual(scim.status_code, 200)
        self.assertIn('Resources', scim.data)

    def test_compliance_evidence_and_vuln_sla(self):
        self.login('admin', 'AdminPass123!')
        evidence = self.client.post(
            '/api/v1/compliance/evidence-packs/',
            {
                'control': 'encryption',
                'title': 'Field encryption key management',
                'status': 'ready',
                'owner': 'Security',
            },
            format='json',
        )
        self.assertEqual(evidence.status_code, 201)
        self.assertEqual(ComplianceEvidencePack.objects.count(), 1)

        vuln = self.client.post(
            '/api/v1/compliance/vulnerabilities/',
            {
                'title': 'Outdated dependency',
                'severity': 'high',
                'status': 'open',
                'discovered_at': date.today().isoformat(),
            },
            format='json',
        )
        self.assertEqual(vuln.status_code, 201)
        finding = VulnerabilityFinding.objects.get()
        self.assertEqual(finding.due_at, finding.discovered_at + timedelta(days=14))

    def test_payroll_reconciliation(self):
        today = date.today()
        Salary.objects.create(
            employee=self.employee,
            month=today.month,
            year=today.year,
            basic_salary=1_000_000,
            allowances=0,
            deductions=0,
            tax=50_000,
            gross_salary=1_000_000,
            nssf_employee=50_000,
            nssf_employer=100_000,
        )
        self.login('manager', 'ManagerPass123!')
        response = self.client.get(
            f'/api/v1/payroll/reconciliation/?month={today.month}&year={today.year}',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['totals']['employees'], 1)

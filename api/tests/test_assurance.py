from io import StringIO

from django.core.management import call_command

from api.assurance import update_loadtest_evidence_pack
from compliance.models import ComplianceEvidencePack

from .base import HRAPITestCase


class AssuranceEvidenceTests(HRAPITestCase):
    def test_seed_includes_new_assurance_controls(self):
        call_command('seed_compliance_evidence', stdout=StringIO())
        controls = set(ComplianceEvidencePack.objects.values_list('control', flat=True))
        for required in (
            'penetration_testing',
            'change_management',
            'availability_slo',
            'access_reviews',
        ):
            self.assertIn(required, controls)

    def test_record_loadtest_evidence_command(self):
        call_command(
            'record_loadtest_evidence',
            ok=True,
            requests=100,
            error_rate=0.001,
            median_ms=50,
            p95_ms=120,
            notes='unit test',
            stdout=StringIO(),
        )
        pack = ComplianceEvidencePack.objects.get(
            control='availability_slo',
            title='Load / soak test evidence',
        )
        self.assertEqual(pack.status, 'ready')
        self.assertIn('requests=100', pack.description)

    def test_record_assurance_event_command(self):
        call_command(
            'record_assurance_event',
            control='penetration_testing',
            title='External pen-test',
            ok=True,
            description='No critical findings',
            evidence_url='https://example.com/report.pdf',
            stdout=StringIO(),
        )
        pack = ComplianceEvidencePack.objects.get(
            control='penetration_testing',
            title='External pen-test',
        )
        self.assertEqual(pack.status, 'ready')
        self.assertEqual(pack.evidence_url, 'https://example.com/report.pdf')

    def test_loadtest_helper_marks_gap_on_failure(self):
        pack = update_loadtest_evidence_pack(
            ok=False,
            requests=20,
            error_rate=0.2,
            median_ms=900,
            p95_ms=2000,
            notes='failed soak',
        )
        self.assertEqual(pack.status, 'gap')

    def test_evidence_api_accepts_new_controls(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.post(
            '/api/v1/compliance/evidence-packs/',
            {
                'control': 'access_reviews',
                'title': 'Q1 access review',
                'status': 'ready',
                'owner': 'Security',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['control_label'], 'Access reviews')

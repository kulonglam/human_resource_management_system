"""OpenAPI schema and lightweight API latency smoke tests."""
import os
import time
from pathlib import Path

from .base import HRAPITestCase

OPENAPI_SNAPSHOT = Path(__file__).resolve().parent / 'fixtures' / 'openapi_schema.yaml'


class OpenAPISchemaTests(HRAPITestCase):
    def test_schema_endpoint_available(self):
        response = self.client.get('/api/v1/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'openapi', response.content.lower())

    def test_swagger_ui_available(self):
        response = self.client.get('/api/v1/docs/')
        self.assertEqual(response.status_code, 200)

    def test_openapi_schema_matches_snapshot(self):
        response = self.client.get('/api/v1/schema/')
        self.assertEqual(response.status_code, 200)
        current = response.content

        if os.environ.get('UPDATE_OPENAPI_SNAPSHOT') == '1':
            OPENAPI_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
            OPENAPI_SNAPSHOT.write_bytes(current)
            self.skipTest('Snapshot updated; re-run without UPDATE_OPENAPI_SNAPSHOT=1')

        if not OPENAPI_SNAPSHOT.exists():
            self.fail(
                f'Missing OpenAPI snapshot at {OPENAPI_SNAPSHOT}. '
                'Run: UPDATE_OPENAPI_SNAPSHOT=1 python manage.py test api.tests.test_api_contract.OpenAPISchemaTests.test_openapi_schema_matches_snapshot',
            )

        expected = OPENAPI_SNAPSHOT.read_bytes()
        if current != expected:
            self.fail(
                'OpenAPI schema drift detected. If intentional, refresh the snapshot with '
                'UPDATE_OPENAPI_SNAPSHOT=1 python manage.py test '
                'api.tests.test_api_contract.OpenAPISchemaTests.test_openapi_schema_matches_snapshot',
            )


class APILatencySmokeTests(HRAPITestCase):
    """Guard against accidental N+1 or catastrophic slowdown on hot paths."""

    def test_health_responds_quickly(self):
        start = time.perf_counter()
        response = self.client.get('/api/v1/health/')
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed_ms, 500, f'health took {elapsed_ms:.0f}ms')

    def test_authenticated_employee_list_responds_quickly(self):
        self.login('admin', 'AdminPass123!')
        start = time.perf_counter()
        response = self.client.get('/api/v1/employees/')
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed_ms, 2000, f'employees list took {elapsed_ms:.0f}ms')

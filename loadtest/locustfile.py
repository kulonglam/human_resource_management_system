"""
Locust load / soak scenarios for HRMIS.

Usage:
  pip install locust
  locust -f loadtest/locustfile.py --host https://staging.example.com

Smoke (CI / local):
  locust -f loadtest/locustfile.py --host http://127.0.0.1:8000 \
    --headless -u 5 -r 2 -t 30s --csv=loadtest/results --html=loadtest/results.html
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from locust import HttpUser, between, events, task

# Locust adds this file's directory to sys.path; ensure repo root is importable.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from loadtest.thresholds import evaluate_stats, thresholds_from_env  # noqa: E402

ADMIN_USER = os.environ.get('E2E_ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('E2E_ADMIN_PASSWORD', 'Admin@HRMIS2026!')


@events.quitting.add_listener
def _(environment, **_kwargs):
    """Fail the process when CI/smoke thresholds are breached."""
    result = evaluate_stats(environment.stats, thresholds_from_env())
    if not result.ok:
        environment.process_exit_code = 1
        print(f'LOADTEST THRESHOLD FAIL: {result.message}')
    else:
        print(f'LOADTEST THRESHOLD OK: {result.message}')


class HRMISUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.client.get('/api/v1/auth/csrf/')
        response = self.client.post(
            '/api/v1/auth/login/',
            json={'username': ADMIN_USER, 'password': ADMIN_PASSWORD},
            name='/api/v1/auth/login/',
        )
        self.authenticated = response.status_code == 200

    @task(5)
    def health(self):
        self.client.get('/api/v1/health/')

    @task(3)
    def dashboard(self):
        if not self.authenticated:
            return
        self.client.get('/api/v1/dashboard/')

    @task(3)
    def employees(self):
        if not self.authenticated:
            return
        self.client.get('/api/v1/employees/')

    @task(2)
    def leaves(self):
        if not self.authenticated:
            return
        self.client.get('/api/v1/leaves/')

    @task(2)
    def payroll_runs(self):
        if not self.authenticated:
            return
        self.client.get('/api/v1/payroll-runs/')

    @task(2)
    def reports_filters(self):
        if not self.authenticated:
            return
        self.client.get('/api/v1/reports/filters/')

    @task(1)
    def ops_health(self):
        if not self.authenticated:
            return
        self.client.get('/api/v1/ops/slos/')

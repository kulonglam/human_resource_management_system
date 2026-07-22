"""Unit tests for Locust threshold helpers (no Locust runtime required)."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from loadtest.thresholds import Thresholds, evaluate_csv, evaluate_stats


class _FakeTotal:
    def __init__(self, requests, failures, median, p95):
        self.num_requests = requests
        self.num_failures = failures
        self._median = median
        self._p95 = p95

    def get_response_time_percentile(self, pct):
        return self._median if pct <= 0.5 else self._p95


class _FakeStats:
    def __init__(self, requests, failures, median, p95):
        self.total = _FakeTotal(requests, failures, median, p95)


class LoadtestThresholdTests(TestCase):
    def test_passes_within_budget(self):
        result = evaluate_stats(_FakeStats(100, 0, 100, 400), Thresholds())
        self.assertTrue(result.ok)

    def test_fails_on_error_rate(self):
        result = evaluate_stats(_FakeStats(100, 2, 100, 400), Thresholds(max_error_rate=0.005))
        self.assertFalse(result.ok)
        self.assertIn('error_rate', result.message)

    def test_fails_on_insufficient_samples(self):
        result = evaluate_stats(_FakeStats(3, 0, 10, 20), Thresholds(min_requests=10))
        self.assertFalse(result.ok)

    def test_csv_aggregated_row(self):
        csv_body = (
            'Type,Name,Request Count,Failure Count,Median Response Time,95%\n'
            'GET,/api/v1/health/,50,0,40,90\n'
            'None,Aggregated,50,0,40,90\n'
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'results_stats.csv'
            path.write_text(csv_body, encoding='utf-8')
            result = evaluate_csv(path, Thresholds(min_requests=10))
        self.assertTrue(result.ok)
        self.assertEqual(result.total_requests, 50)

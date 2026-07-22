"""Fail Locust / soak runs when error rate or latency budgets are breached."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Thresholds:
    max_error_rate: float = 0.005  # 0.5%
    max_median_ms: float = 800.0
    max_p95_ms: float = 1500.0
    min_requests: int = 10


@dataclass(frozen=True)
class ThresholdResult:
    ok: bool
    message: str
    error_rate: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0
    total_requests: int = 0


def thresholds_from_env() -> Thresholds:
    return Thresholds(
        max_error_rate=float(os.environ.get('LOADTEST_MAX_ERROR_RATE', '0.005')),
        max_median_ms=float(os.environ.get('LOADTEST_MAX_MEDIAN_MS', '800')),
        max_p95_ms=float(os.environ.get('LOADTEST_MAX_P95_MS', '1500')),
        min_requests=int(os.environ.get('LOADTEST_MIN_REQUESTS', '10')),
    )


def evaluate_stats(stats: Any, thresholds: Thresholds | None = None) -> ThresholdResult:
    """Evaluate a Locust Environment.stats (or StatsManager) aggregate."""
    thresholds = thresholds or Thresholds()
    total = stats.total
    num_requests = int(getattr(total, 'num_requests', 0) or 0)
    num_failures = int(getattr(total, 'num_failures', 0) or 0)
    if num_requests < thresholds.min_requests:
        return ThresholdResult(
            ok=False,
            message=(
                f'Insufficient samples: {num_requests} < {thresholds.min_requests} '
                '(is the server up and seed users present?)'
            ),
            total_requests=num_requests,
        )

    error_rate = num_failures / num_requests if num_requests else 1.0
    median_ms = float(total.get_response_time_percentile(0.5) or 0)
    p95_ms = float(total.get_response_time_percentile(0.95) or 0)

    problems = []
    if error_rate > thresholds.max_error_rate:
        problems.append(
            f'error_rate={error_rate:.4f} > {thresholds.max_error_rate}'
        )
    if median_ms > thresholds.max_median_ms:
        problems.append(f'median_ms={median_ms:.0f} > {thresholds.max_median_ms}')
    if p95_ms > thresholds.max_p95_ms:
        problems.append(f'p95_ms={p95_ms:.0f} > {thresholds.max_p95_ms}')

    if problems:
        return ThresholdResult(
            ok=False,
            message='; '.join(problems),
            error_rate=error_rate,
            median_ms=median_ms,
            p95_ms=p95_ms,
            total_requests=num_requests,
        )
    return ThresholdResult(
        ok=True,
        message=(
            f'requests={num_requests} error_rate={error_rate:.4f} '
            f'median_ms={median_ms:.0f} p95_ms={p95_ms:.0f}'
        ),
        error_rate=error_rate,
        median_ms=median_ms,
        p95_ms=p95_ms,
        total_requests=num_requests,
    )


def evaluate_csv(stats_csv: Path, thresholds: Thresholds | None = None) -> ThresholdResult:
    """Evaluate Locust `--csv` aggregated stats (`*_stats.csv` total row)."""
    thresholds = thresholds or Thresholds()
    with stats_csv.open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    total = next((r for r in rows if (r.get('Name') or r.get('name')) == 'Aggregated'), None)
    if not total:
        return ThresholdResult(ok=False, message=f'No Aggregated row in {stats_csv}')

    num_requests = int(float(total.get('Request Count') or total.get('# requests') or 0))
    num_failures = int(float(total.get('Failure Count') or total.get('# failures') or 0))
    median_ms = float(total.get('Median Response Time') or total.get('Median response time') or 0)
    # Locust CSV may expose 95%ile column under different headers across versions.
    p95_ms = float(
        total.get('95%')
        or total.get('95%ile')
        or total.get('Ninety Fifth Response Time')
        or 0
    )
    error_rate = num_failures / num_requests if num_requests else 1.0

    class _FakeTotal:
        def __init__(self):
            self.num_requests = num_requests
            self.num_failures = num_failures

        def get_response_time_percentile(self, pct):
            return median_ms if pct <= 0.5 else p95_ms

    class _Proxy:
        def __init__(self):
            self.total = _FakeTotal()

    return evaluate_stats(_Proxy(), thresholds)


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Check Locust CSV against thresholds')
    parser.add_argument('stats_csv', type=Path, help='Path to *_stats.csv')
    args = parser.parse_args()
    result = evaluate_csv(args.stats_csv, thresholds_from_env())
    print(result.message)
    sys.exit(0 if result.ok else 1)


if __name__ == '__main__':
    main()

# Load / soak tests (Locust)

Scenarios cover health, login, dashboard, employees, leaves, payroll runs, reports filters, and ops SLOs.

## Prerequisites

```bash
pip install locust
# Django must be running and seed users available (seed_data / E2E credentials)
```

## Interactive UI

```bash
locust -f loadtest/locustfile.py --host http://127.0.0.1:8000
```

Open http://localhost:8089 and start a test.

## Headless smoke (CI / local)

```bash
locust -f loadtest/locustfile.py --host http://127.0.0.1:8000 \
  --headless -u 5 -r 2 -t 30s \
  --csv=loadtest/results --html=loadtest/results.html --only-summary
```

The Locust process exits non-zero when thresholds fail (see `loadtest/thresholds.py`):

| Metric | Default max |
|--------|-------------|
| Error rate | 0.5% (`LOADTEST_MAX_ERROR_RATE`) |
| Median latency | 800 ms (`LOADTEST_MAX_MEDIAN_MS`) |
| p95 latency | 1500 ms (`LOADTEST_MAX_P95_MS`) |
| Min requests | 10 (`LOADTEST_MIN_REQUESTS`) |

Re-check a CSV offline:

```bash
python -m loadtest.thresholds loadtest/results_stats.csv
```

Record evidence for auditors:

```bash
python manage.py record_loadtest_evidence --ok --requests 500 --error-rate 0.001 --median-ms 90 --p95-ms 220
```

## Soak guidance

- Staging soak: 20–50 users, 15–60 minutes; watch `/api/v1/ops/slos/` and DB CPU.
- Log results in [SOAK_RESULTS.md](SOAK_RESULTS.md).
- Prefer running against a replica-backed staging DB, not production.
- Longer soak: GitHub Actions → **Run workflow** → set `run_loadtest_soak=true`.

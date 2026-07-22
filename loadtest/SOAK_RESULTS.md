# Soak / load test results log

Fill a row after each staging soak. File the summary into Compliance → Evidence pack control **Availability / SLO**, or run:

```bash
python manage.py record_loadtest_evidence \
  --requests 12000 --error-rate 0.001 --median-ms 120 --p95-ms 480 \
  --notes "Staging soak 30 users / 45m" --url "https://ci.example/artifacts/..."
```

| Date | Environment | Users | Duration | Requests | Error rate | Median ms | p95 ms | Pass? | Operator | Artifact / ticket |
|------|-------------|-------|----------|----------|------------|-----------|--------|-------|----------|-------------------|
| YYYY-MM-DD | staging | 30 | 45m | | | | | | | |
| | | | | | | | | | | |

## Pass criteria (aligns with app SLO)

- Error rate ≤ **0.5%**
- Sustained median ≤ **800 ms** (authenticated list endpoints)
- Sustained p95 ≤ **1500 ms** (CI smoke may use the same budget)
- Watch `/api/v1/ops/slos/` and DB CPU during the run

## CI smoke

Short Locust smoke runs on every `main` push (5 users / 30s). Artifacts: Locust HTML/CSV from the `loadtest` GitHub Actions job.

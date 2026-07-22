# Business continuity plan (BCP)

Complements [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) and [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md).

## Objectives

| Metric | Target | Source |
|--------|--------|--------|
| RTO | ≤ 4 hours for production API | DR doc / restore drills |
| RPO | ≤ 24 hours (backup cadence) | `backup_database` schedule |
| Comms | First stakeholder update ≤ 60 minutes | Incident commander |

## Roles

- **Incident commander** — declares severity, owns timeline.
- **Ops lead** — restore, health/SLO, backups.
- **HR/Payroll lead** — business prioritization (payroll cutover, leave freezes).
- **Communications** — employee/manager notices.

## Continuity order

1. Confirm blast radius (auth, DB, Redis, storage).
2. Fail closed on write-heavy modules if needed (payroll approve, retention purge).
3. Restore DB from latest verified backup (`restore_database` / drill runbook).
4. Bring Redis/cache; restart Gunicorn / `qcluster`.
5. Verify `/api/v1/health/`, login, employee list, payroll read.
6. Resume scheduled tasks; review Ops alerts history.

## Workarounds

- **Read-only mode**: scale workers down; block destructive admin actions via change freeze.
- **Payroll deadline**: export last approved run CSVs from backups if live compute is unavailable.
- **Careers / public apply**: disable careers routes at the edge (WAF/nginx) if abuse or outage.

## Testing

- Monthly DR checks (`run_monthly_dr_checks`).
- Quarterly tabletop using this BCP + incident playbook.
- Annual full restore drill with timed RTO measurement.
- Load / soak: Locust smoke on every `main` CI push; staging soak log in [loadtest/SOAK_RESULTS.md](loadtest/SOAK_RESULTS.md); file results with `record_loadtest_evidence`.

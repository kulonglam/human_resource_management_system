# Disaster Recovery — Avvento HRMIS

This document defines recovery objectives, ownership, and the operational procedures used to prove backups are restorable.

## Recovery objectives

| Metric | Target | Current implementation |
|--------|--------|------------------------|
| **RPO** (Recovery Point Objective) | **168 hours (7 days)** | Weekly encrypted `backup_database` cron on production; optional S3 offsite copy |
| **RTO** (Recovery Time Objective) | **60 minutes** | Documented restore runbook + monthly isolated restore drill on staging |

Targets are configurable via environment variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `DR_RPO_TARGET_HOURS` | `168` | Maximum acceptable age of the latest backup |
| `DR_RTO_TARGET_MINUTES` | `60` | Maximum acceptable restore drill duration |
| `DR_VERIFY_STALE_DAYS` | `35` | Alert if backup verification is older than this |
| `DR_DRILL_STALE_DAYS` | `35` | Alert if restore drill evidence is older than this |

## Scope

**In scope**
- PostgreSQL / SQLite application database
- Encrypted local backups under `backups/`
- Optional S3 backup objects (`BACKUP_S3_BUCKET`)

**Out of scope**
- Render platform outages (mitigated by staging environment + blueprint redeploy)
- Media files unless `AWS_STORAGE_BUCKET_NAME` is configured (restore media separately)
- IdP / SMTP provider outages

## Roles

| Role | Responsibility |
|------|----------------|
| **Ops / HR Admin** | Approve production restore, run staging drills, review Ops Center DR panel |
| **Engineering** | Maintain backup commands, encryption keys, Render cron jobs |
| **Compliance** | Review monthly drill evidence pack |

## Backup schedule

| Job | Environment | Schedule (UTC) | Command |
|-----|-------------|----------------|---------|
| `hrmis-weekly-backup` | Production | Sundays 05:00 | `backup_database && verify_backup` |
| `hrmis-staging-monthly-dr` | Staging | 1st of month 08:00 | `run_monthly_dr_checks` |

## Verification and drills

### Weekly verification (production)

```bash
python manage.py backup_database
python manage.py verify_backup
```

`verify_backup` decrypts the artifact (if encrypted), runs integrity checks, and records a `verify` event in `backups/dr_state.json`.

### Monthly restore drill (staging)

```bash
python manage.py run_monthly_dr_checks
```

This chains:
1. `backup_database` — creates a fresh staging backup
2. `verify_backup` — proves decrypt + dump integrity
3. `run_restore_drill --record-evidence` — restores into an **isolated scratch database** (never the live DB), measures restore time, and updates the compliance evidence pack

SQLite environments perform a full scratch restore. PostgreSQL attempts `createdb` + `pg_restore` into `hrmis_drill_*`; if permissions are unavailable, the drill falls back to verify-only mode and records that outcome.

## Production restore procedure

1. **Declare incident** and assign an incident commander (see [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)).
2. **Stop writes**: scale Render web/worker services to `0` or enable maintenance.
3. **Identify backup**: newest file in `backups/` or S3 (`postgres_*.dump.enc`).
4. **Validate on staging first** (recommended):

```bash
python manage.py verify_backup --path backups/postgres_YYYYMMDD.dump.enc
python manage.py run_restore_drill --path backups/postgres_YYYYMMDD.dump.enc
```

5. **Restore production** (destructive):

```bash
python manage.py restore_database backups/postgres_YYYYMMDD.dump.enc --force
python manage.py migrate --check
```

6. **Smoke test**: `/api/v1/health/`, admin login, payroll list, approvals queue.
7. **Record evidence**: note wall-clock restore time, backup used, and any data loss window for the incident report.

## Monitoring and alerts

- Ops API: `/api/v1/ops/status/` includes a `disaster_recovery` block with RTO/RPO status.
- `check_ops_alerts` emits warnings when verification or drill evidence is stale, RPO is breached, or drill restore time exceeds RTO.
- Compliance evidence: `Monthly restore drill evidence` pack is updated after each successful drill.

## Evidence pack

Run once per environment:

```bash
python manage.py seed_compliance_evidence
```

After each monthly drill, evidence is auto-updated with:
- Drill timestamp
- Backup filename
- Restore mode (`sqlite_scratch_restore`, `postgres_scratch_restore`, or `postgres_verify_only`)
- Measured restore seconds

## Review cadence

| Activity | Frequency |
|----------|-----------|
| Backup verification | Weekly (production cron) |
| Restore drill | Monthly (staging cron) |
| RTO/RPO target review | Quarterly |
| Key rotation drill | Annually or on personnel change |

## Related commands

| Command | Purpose |
|---------|---------|
| `backup_database` | Create encrypted backup |
| `verify_backup` | Decrypt + integrity check without touching live DB |
| `run_restore_drill` | Isolated restore drill with timing |
| `run_monthly_dr_checks` | Backup + verify + drill + evidence |
| `restore_database --force` | Production/staging restore (destructive) |
| `prune_backups` | Local retention enforcement |

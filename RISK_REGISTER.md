# Risk register — FCA HRMIS

Living register of material risks for the HRMIS. Review at least quarterly with ops/security. Update status after incidents (see [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)).

| ID | Risk | Likelihood | Impact | Mitigation in product / process | Owner | Status |
|----|------|------------|--------|----------------------------------|-------|--------|
| R-01 | Unauthorized access to payroll or PII | M | H | RBAC, MFA enforcement, sensitive-field masking, audit + sensitive-access logs | Security | Open — monitor |
| R-02 | Encryption key loss or mis-rotation | L | H | Distinct `FIELD_ENCRYPTION_KEY` / `BACKUP_ENCRYPTION_KEY`; previous-key env vars; require keys in prod | Security | Open — monitor |
| R-03 | Backup restore failure exceeds RTO | M | H | Encrypted backups, `verify_backup`, monthly staging DR drills, [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) | Ops | Open — monitor |
| R-04 | Accidental purge of needed audit/compliance data | L | M | Retention policies UI, `--dry-run`, scheduled purge with audit log, inactive policies | Compliance | Open — monitor |
| R-05 | Incorrect statutory PAYE/NSSF filing | M | H | Locked payroll runs, statutory export, payroll-day runbook, variance checks | HR/Finance | Open — monitor |
| R-06 | Credential stuffing / brute-force login | M | M | Login throttle, lockout threshold/window, MFA for privileged roles | Security | Open — monitor |
| R-07 | Dependency or host vulnerability (Render/OS/libs) | M | M | `VulnerabilityFinding` SLA tracker, pin requirements, Render platform patches | Security | Open — monitor |
| R-08 | Webhook secret or SSO misconfiguration | L | M | Signed webhooks, dashboard secrets, SSO env isolation staging vs prod | Ops | Open — monitor |
| R-09 | Observability gap delays detection | M | M | Sentry, `check_ops_alerts`, health/SLO endpoints, `HR_NOTIFY_EMAIL` | Ops | Open — monitor |
| R-10 | Incomplete GDPR erasure / export | L | H | Subject export + admin erasure APIs, compliance settings UI | Compliance | Open — monitor |

**Status values:** `Open — monitor` · `Mitigating` · `Accepted` · `Closed`

When accepting a risk, record rationale and review date in the compliance evidence pack or change ticket.

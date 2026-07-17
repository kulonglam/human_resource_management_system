# Incident response playbook — FCA HRMIS

Operational guide for detecting, containing, and recovering from security, privacy, and payroll incidents. Complements [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) (outage / restore) and in-app Ops runbooks at `/settings/ops`.

## 1. Roles

| Role | Responsibility |
|------|----------------|
| **Incident commander (IC)** | Owns severity, decisions, and timeline; usually on-call ops or HR admin |
| **Technical lead** | Investigation, containment, evidence (logs, backups, Sentry) |
| **Communications** | Internal stakeholders and (if required) affected individuals / regulators |
| **Compliance owner** | Retention, GDPR erasure/export, evidence pack updates |

Keep a current on-call contact list outside this repo (password manager or ops wiki).

## 2. Severity

| Level | Examples | Response target |
|-------|----------|-----------------|
| **SEV-1** | Confirmed data breach; ransomware; production DB destroyable; payroll paid incorrectly at scale | IC + tech lead immediately; halt risky jobs |
| **SEV-2** | Suspected credential compromise; MFA bypass attempt; SLO/health critical >30 min; statutory export wrong | Same-day containment |
| **SEV-3** | Single-user account lockout storm; webhook failures; leave backlog spike | Next business day |
| **SEV-4** | Cosmetic / docs / non-prod only | Backlog |

Escalate upward if impact or confidence increases.

## 3. First 30 minutes (all SEV-1/2)

1. **Declare** the incident (chat/ticket): title, severity, IC, start time.
2. **Preserve evidence** — do not wipe logs; note wall-clock times (UTC).
3. **Contain** without destroying forensics:
   - Rotate compromised secrets (`SECRET_KEY` only after session invalidation plan; always rotate `FIELD_ENCRYPTION_KEY` / `BACKUP_ENCRYPTION_KEY` carefully — see §5).
   - Disable public registration if enabled (`ALLOW_PUBLIC_REGISTRATION=False`).
   - Force password resets / disable accounts via Django admin or SCIM for affected users.
   - Scale workers/cron down if a bad job is looping.
4. **Health check**: `GET /api/v1/health/` and Ops Center `/settings/ops`.
5. **Notify** `HR_NOTIFY_EMAIL` / leadership for SEV-1/2.

## 4. Playbooks by type

### 4.1 Credential or session compromise

1. Identify affected usernames from audit logs (`/audit-logs`) and failed-login lockouts.
2. Disable or reset passwords; revoke API keys if used.
3. Confirm MFA status for admins/managers/payroll (`ENFORCE_MFA_*`).
4. Review `AuditLog` and sensitive-access logs for unauthorized exports.
5. If session cookie theft suspected: rotate `SECRET_KEY` and restart web + workers (invalidates sessions).

### 4.2 Suspected or confirmed personal data breach

1. Classify data (PII / payroll / national ID / bank) and approximate record count.
2. Freeze destructive retention runs until legal/compliance clears purge:  
   `python manage.py apply_retention_policies --dry-run` only; do not purge.
3. Export subject packages if individuals request access (`/settings/security` or GDPR API).
4. Document timeline for the compliance evidence pack (`incident_response` control).
5. Follow local breach-notification law (Uganda / GDPR if EU data subjects apply). Legal owns external notices.

### 4.3 Payroll / statutory incident

Use Ops runbook **Payroll processing day**, then:

1. Halt further `approve` / `mark-paid` on the bad run.
2. Compare payslips vs prior month; export PAYE/NSSF for the period and archive a report snapshot.
3. If money moved incorrectly: finance + bank recall process (outside app).
4. Fix root cause (attendance lock, tax tables, wrong employee bank data) before re-run.
5. If >1% of payslips are wrong → treat as **SEV-1** until corrected.

### 4.4 Availability / data loss

Follow [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md):

1. Confirm backup freshness via Ops DR panel / `verify_backup`.
2. Prefer staging restore drill before production `restore_database … --force`.
3. Record RTO/RPO evidence after recovery.

### 4.5 Malware / ransomware on operator workstation

1. Assume tokens/passwords on that machine are burned.
2. Rotate Render env secrets from a clean device; rotate SSO app secrets if exposed.
3. Do **not** restore production from a backup created *after* encryption/malware indicators without forensics advice.

## 5. Secrets and key rotation notes

| Secret | Notes |
|--------|-------|
| `SECRET_KEY` | Rotating logs everyone out; coordinate maintenance window |
| `FIELD_ENCRYPTION_KEY` | Set previous key in `FIELD_ENCRYPTION_KEY_PREVIOUS` before rotating; re-encrypt or dual-read as implemented |
| `BACKUP_ENCRYPTION_KEY` | Keep prior keys in `BACKUP_ENCRYPTION_KEY_PREVIOUS` until old backups age out |
| SMTP / OAuth / AWS | Rotate at provider; update Render env; restart services |
| `SEED_*_PASSWORD` | Only for bootstrap; never reuse as ongoing admin password |

Never commit secrets. Prefer Render dashboard / vault over `.env` in production.

## 6. Communications template (internal)

```
INCIDENT: <short title>
Severity: SEV-n
IC: <name>
Started (UTC): <timestamp>
Impact: <users / payroll / data>
Status: Investigating | Contained | Recovering | Closed
Next update: <time>
```

External notices require legal review — do not invent regulatory language in tickets.

## 7. Close-out (post-incident review)

Within 5 business days of SEV-1/2 closure:

1. Timeline of detection → containment → recovery.
2. Root cause and contributing factors.
3. What worked / what failed (alerting, MFA, backups, runbooks).
4. Action items with owners and due dates (track as `VulnerabilityFinding` or tickets).
5. Update compliance evidence:  
   `python manage.py seed_compliance_evidence` (if missing) and mark `incident_response` pack reviewed in `/settings/compliance`.
6. Link the write-up from the Ops Center notes or evidence URL field.

## 8. Related commands and endpoints

| Action | Command / URL |
|--------|----------------|
| Health | `GET /api/v1/health/` |
| Ops / runbooks | `GET /api/v1/ops/status/` · UI `/settings/ops` |
| Ops alerts | `python manage.py check_ops_alerts` |
| Retention preview / purge | `python manage.py apply_retention_policies [--dry-run]` |
| Backup verify / restore | see `DISASTER_RECOVERY.md` |
| Env reference | [ENV.md](ENV.md) |
| Risk register | [RISK_REGISTER.md](RISK_REGISTER.md) |

## 9. Testing this playbook

- Quarterly tabletop: walk a SEV-2 credential scenario with IC + tech lead.
- Monthly: staging DR checks (`run_monthly_dr_checks`) already exercise backup evidence.
- After major releases: confirm `HR_NOTIFY_EMAIL` and `SENTRY_DSN` still deliver ops alerts.

# Enterprise readiness scorecard

**Deployment model:** single organization (one employer). English UI only.  
`Organization` FK / tenancy helpers are optional infrastructure, not a multi-tenant product.

## Engineering 10/10 (in-repo)

| Area | Status | Proof |
|------|--------|-------|
| HR domain + transactional integrity | Done | Domain services + API tests |
| Security baselines | Done | MFA gates, encryption keys, headers, lockout, RBAC |
| Continuous security CI | Done | pip/npm audit, Gitleaks, ZAP, Bandit |
| DR / BCP | Done | Backup encrypt/verify, restore drills, BCP docs |
| Ops observability | Done | Health/SLO, durable alerts, Ops Center |
| Load proof | Done | Locust + CI thresholds + soak log |
| Compliance evidence ops | Done | Evidence packs + assurance commands |
| Mobile / devices / SCIM | Done | PWA clock, device ingest, rich SCIM |
| E2E critical paths | Done | Auth, leave, payroll, MFA, approvals, mobile, devices |

## External / organizational (cannot be coded)

| Item | Owner | Evidence hook |
|------|-------|---------------|
| Third-party penetration test report | Security vendor + org | Control `penetration_testing` |
| SOC 2 / ISO certification letter | Auditor + org | [COMPLIANCE_CONTROLS.md](COMPLIANCE_CONTROLS.md) + evidence packs |
| Production soak under real traffic | Ops | [loadtest/SOAK_RESULTS.md](loadtest/SOAK_RESULTS.md) |
| Privileged access reviews | Security/HR | Control `access_reviews` |
| Vendor SOC reports (IdP, host, S3) | Procurement | Attach to evidence packs |

## Seed evidence packs

```bash
python manage.py seed_compliance_evidence
python manage.py record_assurance_event --control penetration_testing --title "Annual pen-test 2026" --gap
```

See [SECURITY_ASSURANCE.md](SECURITY_ASSURANCE.md).

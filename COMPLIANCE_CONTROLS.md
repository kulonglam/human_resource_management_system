# SOC 2 / ISO 27001 control mapping

This maps common Trust Services Criteria / ISO 27001 themes to concrete HRMIS controls. It is an implementation aid, not a certification attestation.

| Theme | Control intent | HRMIS evidence |
|-------|----------------|----------------|
| CC6 Access control | Unique accounts, least privilege | Roles + permissions (`accounts.Role`), MFA flags, `PermissionRoute` / DRF permissions |
| CC6 Privileged access | Admin actions limited | Admin-only Ops, users, audit export; payroll MFA gates |
| CC7 Logging / monitoring | Detect anomalies | `AuditLog`, `SensitiveDataAccessLog`, Sentry, Ops alerts + durable `OpsAlertEvent` |
| CC7 Incident response | Documented response | [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md), Ops runbooks |
| CC8 Change management | Controlled releases | GitHub CI (tests, audits, ZAP, Gitleaks, Bandit), OpenAPI contract tests; evidence control `change_management` |
| CC9 Risk mitigation | Identified risks tracked | [RISK_REGISTER.md](RISK_REGISTER.md) |
| A1 Availability | RTO/RPO + backups + load proof | [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md), Locust CI + [loadtest/SOAK_RESULTS.md](loadtest/SOAK_RESULTS.md), control `availability_slo` |
| C1 Confidentiality | Protect PII | Field encryption, document access rules, GDPR export/erasure |
| P1 Privacy | Retention / rights | Retention policies + `apply_retention_policies`, compliance exports |
| ISO A.8 Assets | Inventory | [DATA_DICTIONARY.md](DATA_DICTIONARY.md), asset module |
| ISO A.12 Ops security | Hardening | Security headers middleware, nginx/WAF guidance, secrets rotation |
| ISO A.17 Continuity | BCP | [BUSINESS_CONTINUITY.md](BUSINESS_CONTINUITY.md) |

## Evidence packs

Seedable packs live under compliance evidence APIs / `seed_compliance_evidence`. Link tickets and screenshots into those packs during audits.

## Assurance program

Operational playbook: [SECURITY_ASSURANCE.md](SECURITY_ASSURANCE.md). Scorecard: [ENTERPRISE_READINESS.md](ENTERPRISE_READINESS.md).

Additional evidence controls: `penetration_testing`, `change_management`, `availability_slo`, `access_reviews` (seed via `seed_compliance_evidence`; update via `record_assurance_event` / `record_loadtest_evidence`).

## Gaps vs certification

External pen-test reports, formal risk acceptance boards, and vendor SOC reports remain outside the application and must be filed by the organization (see ENTERPRISE_READINESS external checklist).

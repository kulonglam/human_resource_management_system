# Security assurance program

Continuous and periodic controls for a **single-organization** HRMIS deployment. Maps to Compliance evidence packs at `/settings/compliance`.

## Continuous (CI)

| Control | Where | Fail policy |
|---------|-------|-------------|
| Dependency vulns | `pip-audit`, `npm audit` | Fail on known high+ (allowlist in `security/`) |
| Secrets | Gitleaks | Fail on leak |
| DAST baseline | OWASP ZAP | Fail per `.zap/rules.tsv` / `security/zap-rules.tsv` |
| SAST | Bandit (`-ll`) | Fail on Medium/High |
| AuthZ / headers | `api/tests/test_security.py` | Fail suite |

See [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Periodic

| Activity | Cadence | Evidence control | How to file |
|----------|---------|------------------|-------------|
| Penetration test (external) | Annual (or after major auth/payroll changes) | `penetration_testing` | Upload report URL; `python manage.py record_assurance_event --control penetration_testing --title "…" --ok --url …` |
| Privileged access review | Quarterly | `access_reviews` | Review admin/manager/payroll roles; record with `--control access_reviews` |
| Load / soak | Monthly staging + every `main` CI smoke | `availability_slo` | [loadtest/SOAK_RESULTS.md](loadtest/SOAK_RESULTS.md); `record_loadtest_evidence` |
| DR restore drill | Monthly | `backup_restore` | `run_restore_drill --record-evidence` |
| Secrets rotation | Per [SECRETS_ROTATION.md](SECRETS_ROTATION.md) | `encryption` / ops ticket | Update pack notes + rotate env secrets |

## Severity SLAs (VulnerabilityFinding)

| Severity | Remediate within |
|----------|------------------|
| Critical | 7 days |
| High | 14 days |
| Medium | 30 days |
| Low | 90 days |

Track findings in Compliance → Vulnerability SLAs (or API `/api/v1/compliance/vulnerabilities/`).

## Pen-test scope (suggested)

In scope: auth/MFA/SSO, session/CSRF, RBAC on employees/payroll/leave, file uploads, SCIM/API keys, export endpoints, admin Ops, public careers if enabled.

Out of scope by default: social engineering of staff, destructive DoS against production, third-party IdP infrastructure.

## Remediation workflow

1. Log finding as `VulnerabilityFinding` (severity + due date auto-SLA).
2. Fix or accept risk with rationale in the finding / risk register.
3. Re-test; mark finding resolved; update evidence pack status to `ready`.
4. Link CI artifact or ticket URL on the pack (`evidence_url`).

## Related docs

- [COMPLIANCE_CONTROLS.md](COMPLIANCE_CONTROLS.md) — SOC 2 / ISO mapping
- [RISK_REGISTER.md](RISK_REGISTER.md)
- [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)
- [ENTERPRISE_READINESS.md](ENTERPRISE_READINESS.md)

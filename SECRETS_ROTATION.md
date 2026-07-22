# Secrets rotation runbook

Rotate credentials on a schedule (recommended ≤ 90 days) and immediately after any suspected exposure.

## Inventory

| Secret | Env var | Notes |
|--------|---------|-------|
| Django signing | `SECRET_KEY` | Invalidates sessions/CSRF on rotate |
| Field encryption | `FIELD_ENCRYPTION_KEY` | Re-encrypt PII before discarding old key |
| Backup encryption | `BACKUP_ENCRYPTION_KEY` | Keep previous key until old backups expire |
| Database | `DATABASE_URL` / Postgres password | Rotate via host; update PgBouncer |
| Redis | `REDIS_URL` | Invalidate cache/broker briefly |
| SSO / OIDC | IdP client secret | Rotate in IdP then app env |
| Webhook signing | `WebhookEndpoint.secret` | Per-endpoint; notify consumers |
| API keys | `APIKey` hashes | Revoke + issue new; never store plaintext |

## Procedure

1. **Announce** maintenance window if session invalidation is expected.
2. **Generate** new secret (`python -c "import secrets; print(secrets.token_urlsafe(48))"`).
3. **Update** Render/K8s secret store (`hrmis-secrets`) — never commit values.
4. **Deploy** with the new env; confirm `/api/v1/health/` is ok.
5. **Verify** login, MFA, payroll export, webhook delivery.
6. **Retire** old secret from vault after soak period (24h for `SECRET_KEY`; encryption keys follow re-encrypt completion).
7. **Record** rotation in the audit log / change ticket.

## Field encryption key rotation

1. Keep old key available as `FIELD_ENCRYPTION_KEY_PREVIOUS` only if your decrypt path supports dual-key (otherwise plan a batch re-encrypt first).
2. Run `python manage.py encrypt_employee_pii` (or successor) against the new key.
3. Spot-check employee PII reads for admins with `sensitive.view`.
4. Remove previous key after verification.

## Emergency revoke

- Disable compromised API keys in Integrations settings.
- Rotate `SECRET_KEY` + force logout (session cookies become invalid).
- Rotate DB password and Redis URL.
- Follow [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md).

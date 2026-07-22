# Vendor exit / migration guide

Use when leaving a host (e.g. Render), IdP, object storage, or replacing HRMIS itself.

## Data export paths

| Data | Method |
|------|--------|
| Employee GDPR package | `/api/v1/compliance/data-export/...` or UI Compliance |
| Audit logs | `/api/v1/audit-logs/export.csv` / `.xlsx` |
| Full DB | Encrypted backup via `backup_database` + offsite copy |
| Documents | Media volume / S3 bucket sync |
| Webhook history | Integrations delivery log API |

## Dependency inventory

- **Runtime**: Django, DRF, Gunicorn, Django-Q, Redis (optional), Postgres
- **Frontend**: React SPA (Vite build into Django static)
- **Auth**: Session cookies; optional SSO; MFA (TOTP)
- **Observability**: Sentry DSN (optional)
- **Edge**: Cloudflare/WAF + nginx (see `deploy/nginx.conf`)

## Migration checklist

1. Freeze writes (maintenance window).
2. Take final encrypted backup; verify with `verify_backup`.
3. Export compliance packs for legal hold employees.
4. Provision target Postgres; restore; run migrations if schema differs.
5. Reconfigure env ([ENV.md](ENV.md)): `DATABASE_URL`, secrets, Redis, `ALLOWED_HOSTS`, CSRF origins.
6. Cut DNS / Render custom domain; warm caches.
7. Rotate secrets post-cutover ([SECRETS_ROTATION.md](SECRETS_ROTATION.md)).
8. Decommission old host after retention period; scrub media.

## Exit from HRMIS product

1. Export DB + media + OpenAPI schema snapshot.
2. Map tables via [DATA_DICTIONARY.md](DATA_DICTIONARY.md).
3. Replay domain outbox topics (`events.DomainEvent`) if integrating downstream systems.
4. Revoke all API keys and webhook secrets.

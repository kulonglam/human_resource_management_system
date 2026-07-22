# Environment variable reference — FCA HRMIS

Canonical list of configuration read by `avvento_hrmis/settings.py` and related ops tooling. Set secrets in the Render dashboard (or a vault), not in git. See also [DEPLOY.md](DEPLOY.md) for deploy workflow and [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) for rotation after compromise.

Legend: **Required (prod)** = must be set for a safe production deploy · **Optional** = has a sensible default · **Secret** = never commit.

---

## Core / Django

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `SECRET_KEY` | Yes (Secret) | Dev-only fallback | Blueprint auto-generates. Rotating invalidates sessions. |
| `DEBUG` | Yes | `False` when `DATABASE_URL` set, else `True` | Always `False` on staging/production. |
| `DATABASE_URL` | Yes on Render | — | Postgres URL from Render database. |
| `DATABASE_REPLICA_URL` | Optional | — | Read replica URL; enables `PrimaryReplicaRouter`. |
| `USE_PGBOUNCER` | Optional | `False` | When `True`, forces `CONN_MAX_AGE=0` for transaction pooling. |
| `DB_CONN_MAX_AGE` | Optional | `600` | Ignored when `USE_PGBOUNCER=True`. |
| `POSTGRES_NAME` / `USER` / `PASSWORD` / `HOST` / `PORT` | Local Postgres alt | — | Used when `DATABASE_URL` unset. |
| `ALLOWED_HOSTS` | Custom domains | — | Comma-separated. Render hostname added automatically. |
| `CSRF_TRUSTED_ORIGINS` | Custom domains | — | Comma-separated `https://…` origins. |
| `RENDER_EXTERNAL_HOSTNAME` | Auto | — | Set by Render. |
| `RENDER_SERVICE_NAME` | Recommended | — | e.g. `production` / `staging` (Sentry environment). |
| `SECURE_SSL_REDIRECT` | Optional | `True` when not DEBUG | |
| `SECURE_HSTS_SECONDS` | Optional | `31536000` | |
| `CONTENT_SECURITY_POLICY` | Optional | Built-in policy string | Override only if you know the impact. |
| `SESSION_COOKIE_AGE` | Optional | `28800` (8h) | Seconds. |
| `SESSION_IDLE_TIMEOUT_SECONDS` | Optional | `1800` | |
| `LOGIN_LOCKOUT_THRESHOLD` | Optional | `5` | |
| `LOGIN_LOCKOUT_WINDOW_SECONDS` | Optional | `900` | |
| `MAX_UPLOAD_BYTES` | Optional | `10485760` (10 MiB) | |

## Bootstrap / seed

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `SEED_ADMIN_PASSWORD` | First deploy (Secret) | — | Creates initial admin via `bootstrap_admin`; required for hosted `seed_data` create/reset. |
| `SEED_MANAGER_PASSWORD` | Hosted seed create/reset | — | Required when `DATABASE_URL` is set and seeding/resetting manager. |
| `SEED_EMPLOYEE_PASSWORD` | Hosted seed create/reset | — | Required when `DATABASE_URL` is set and seeding/resetting employee. |
| `ALLOW_DEFAULT_SEED_PASSWORDS` | Demos only | unset | Set `1`/`true` to allow published local demo passwords on a hosted DB. |

## Auth / MFA / registration

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `ALLOW_PUBLIC_REGISTRATION` | Yes | `False` | Keep false in production. |
| `ENFORCE_MFA_FOR_ADMINS` | Yes | `True` when `DATABASE_URL` set | |
| `ENFORCE_MFA_FOR_MANAGERS` | Yes | `True` when `DATABASE_URL` set | |
| `ENFORCE_MFA_FOR_PAYROLL` | Yes | `True` when `DATABASE_URL` set | |

## Email

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `EMAIL_BACKEND` | Optional | SMTP when configured, else console | |
| `EMAIL_HOST` | For real mail | — | |
| `EMAIL_PORT` | Optional | `587` | |
| `EMAIL_HOST_USER` | Secret | — | |
| `EMAIL_HOST_PASSWORD` | Secret | — | |
| `EMAIL_USE_TLS` | Optional | `True` | |
| `DEFAULT_FROM_EMAIL` | Recommended | `noreply@hrmis.local` | |
| `HR_NOTIFY_EMAIL` | Recommended | — | Leave/expense alerts + ops/SLO alerts. |

## SSO

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `GOOGLE_OAUTH_CLIENT_ID` / `_SECRET` | If Google SSO | — | Secrets. |
| `MICROSOFT_OAUTH_CLIENT_ID` / `_SECRET` | If Microsoft SSO | — | Secrets. |
| `MICROSOFT_OAUTH_TENANT` | Optional | `common` | |
| `SSO_CALLBACK_BASE_URL` | If SSO | `http://localhost:8000` | Public API origin. |
| `SSO_FRONTEND_REDIRECT` | If SSO | `http://localhost:5173/dashboard` | |
| `SSO_AUTO_PROVISION` | Optional | `False` | |

## Encryption & backups

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `FIELD_ENCRYPTION_KEY` | Yes (Secret) | — | PII at rest. |
| `FIELD_ENCRYPTION_KEY_PREVIOUS` | Rotation | — | Comma-separated prior keys. |
| `REQUIRE_FIELD_ENCRYPTION_KEY` | Recommended | `True` when not DEBUG | Fail closed without key. |
| `ENCRYPT_BACKUPS` | Yes | `True` when not DEBUG | |
| `BACKUP_ENCRYPTION_KEY` | Strongly recommended (Secret) | Falls back to field key | Prefer distinct key. |
| `BACKUP_ENCRYPTION_KEY_PREVIOUS` | Rotation | — | |
| `REQUIRE_BACKUP_ENCRYPTION_KEY` | Optional | See settings | Refuse encrypt without dedicated key when `True`. |
| `BACKUP_S3_BUCKET` | Optional | — | Offsite; upload fail-closed when set. |
| `BACKUP_S3_PREFIX` | Optional | `hrmis-backups/` | |
| `BACKUP_S3_SSE` | Optional | `AES256` | or `aws:kms` |
| `BACKUP_S3_SSE_KMS_KEY_ID` | If KMS | — | |
| `BACKUP_RETENTION_COUNT` | Optional | `14` | Local files; `0` disables. |
| `BACKUP_RETENTION_DAYS` | Optional | `30` | Local files; `0` disables. |

## Object storage (media)

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `AWS_STORAGE_BUCKET_NAME` | If S3 media | — | Enables S3 storage backend. |
| `AWS_S3_REGION_NAME` | Optional | `us-east-1` | |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Secret | — | |
| `AWS_S3_CUSTOM_DOMAIN` | Optional | — | CDN/custom domain. |

## Redis / workers

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `REDIS_URL` | Recommended | — | Cache + django-q broker; LocMem/ORM fallback without it. |
| `Q_WORKERS` | Optional | `2` | django-q worker processes. |

## DR / observability

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `DR_RTO_TARGET_MINUTES` | Optional | `60` | |
| `DR_RPO_TARGET_HOURS` | Optional | `168` | Weekly backup cadence. |
| `DR_VERIFY_STALE_DAYS` | Optional | `35` | Alert if verify older. |
| `DR_DRILL_STALE_DAYS` | Optional | `35` | Alert if drill older. |
| `SENTRY_DSN` | Recommended (Secret) | — | Errors + ops alert messages. |
| `SENTRY_TRACES_SAMPLE_RATE` | Optional | `0.1` | |
| `OPS_ALERT_COOLDOWN_MINUTES` | Optional | `30` | Dedupe health/SLO alerts. |
| `SLO_ALERT_MIN_REQUESTS` | Optional | `25` | Min hourly requests before SLO alert. |

## API throttling

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `API_THROTTLE_ANON` | Optional | `60/minute` | |
| `API_THROTTLE_USER` | Optional | `600/minute` | |
| `API_THROTTLE_LOGIN` | Optional | `10/minute` | |
| `API_THROTTLE_MFA` | Optional | `10/minute` | |
| `API_THROTTLE_EXPORT` | Optional | `30/minute` | |
| `API_THROTTLE_SCIM` | Optional | `60/minute` | |

## Integrations

| Variable | Required (prod) | Default | Notes |
|----------|-----------------|---------|-------|
| `WEBHOOKS_ENABLED` | Optional | `True` | |

## Local / CI only (examples)

| Variable | Notes |
|----------|-------|
| `E2E_BASE_URL` | Playwright base URL |
| `E2E_PYTHON` | Python for MFA prepare command in E2E |
| `E2E_ADMIN_USER` / `E2E_ADMIN_PASSWORD` | Override seed credentials in tests |
| `UPDATE_OPENAPI_SNAPSHOT` | Set `1` to refresh OpenAPI fixture |
| `FIELD_ENCRYPTION_KEY` in CI | Test key; not production |

---

## Quick production checklist

1. `SECRET_KEY`, `DATABASE_URL`, `DEBUG=False`
2. `FIELD_ENCRYPTION_KEY` (+ prefer `BACKUP_ENCRYPTION_KEY`)
3. `ENFORCE_MFA_FOR_*` = `True`, `ALLOW_PUBLIC_REGISTRATION=False`
4. SMTP + `HR_NOTIFY_EMAIL`
5. `REDIS_URL` (blueprint shared group)
6. `SENTRY_DSN`
7. Optional: SSO, `BACKUP_S3_BUCKET`, custom domain hosts/CSRF

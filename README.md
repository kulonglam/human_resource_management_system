# FCA Human Resource Management System (HRMIS)

Django REST API + React SPA for HR operations. The UI is fully React; Django serves the API, admin, and media files.

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6, Django REST Framework |
| Frontend | React 18, Vite, React Router |
| Database | PostgreSQL (production) / SQLite (local fallback) |
| Deploy | Render (`render.yaml`) |

## Project layout

```
api/                 REST API (auth, viewsets, reports)
avvento_hrmis/       Django project settings, SPA catch-all route
frontend/            React application (src/, dist/ after build)
accounts/ … discipline/   HR domain apps (models, admin, migrations only)
```

## Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- PostgreSQL (optional locally; SQLite works for development)

## Local development

**Quick start (recommended):**

```powershell
python -m venv hrmis_env
hrmis_env\Scripts\activate
pip install -r requirements.txt
.\setup-local.ps1
```

Then open **two terminals**:

| Terminal | Command |
|----------|---------|
| Backend | `.\start-backend.ps1` |
| Frontend | `cd frontend` → `npm install` → `npm run dev` |

Open **http://localhost:5173** — Vite proxies API requests to Django on port 8000.

Both servers must be running. If the frontend shows connection errors, start the backend first.

### Manual setup

### 1. Backend

```powershell
python -m venv hrmis_env
hrmis_env\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data --reset-password
python manage.py seed_workflows
```

### 2. Frontend (hot reload)

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies API requests to Django.

Run Django in a second terminal:

```powershell
python manage.py runserver
```

### 3. Production-style local run

Serve everything from Django on one port:

```powershell
cd frontend && npm run build && cd ..
python manage.py runserver
```

Open **http://localhost:8000**

## Default login (after `seed_data`)

| Role | Username | Password (local default) |
|------|----------|-------------------------|
| Admin | `admin` | `Admin@HRMIS2026!` |
| Manager | `manager` | `Manager@HRMIS2026!` |
| Employee | `employee` | `Employee@HRMIS2026!` |

On Render, passwords come from `SEED_*_PASSWORD` env vars (see `render.yaml`).

Reset locally anytime:

```powershell
python manage.py seed_data --reset-password
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret (required in production) |
| `DEBUG` | `True` for local dev, `False` on Render |
| `DATABASE_URL` | PostgreSQL connection string (Render sets this) |
| `SEED_ADMIN_PASSWORD` | Admin password for seed command (Render) |
| `SEED_MANAGER_PASSWORD` | Manager password for seed command |
| `SEED_EMPLOYEE_PASSWORD` | Employee password for seed command |
| `ALLOW_PUBLIC_REGISTRATION` | Set `True` to allow public sign-up (default: `False`) |
| `ENFORCE_MFA_FOR_ADMINS` | Require TOTP MFA for admin accounts (default: `True` on Render/production, `False` for local SQLite) |
| `HR_NOTIFY_EMAIL` | HR inbox for new leave/expense alerts |
| `EMAIL_BACKEND` | Django email backend (default: console for dev) |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP settings for production email |
| `SENTRY_DSN` | Optional Sentry error tracking DSN |
| `SENTRY_TRACES_SAMPLE_RATE` | Sentry performance sampling (default: `0.1`) |
| `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` | Google SSO (optional) |
| `MICROSOFT_OAUTH_CLIENT_ID` / `MICROSOFT_OAUTH_CLIENT_SECRET` / `MICROSOFT_OAUTH_TENANT` | Microsoft SSO (optional; tenant defaults to `common`) |
| `SSO_CALLBACK_BASE_URL` | Backend base URL for OAuth callbacks (e.g. `https://your-app.onrender.com`) |
| `SSO_FRONTEND_REDIRECT` | SPA URL after successful SSO (e.g. `https://your-app.onrender.com/dashboard`) |
| `SSO_AUTO_PROVISION` | Auto-create users on first SSO login (default: `False`) |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket for media uploads (optional; local `media/` when unset) |
| `AWS_S3_REGION_NAME` | S3 region (default: `us-east-1`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 credentials when not using IAM roles |
| `AWS_S3_CUSTOM_DOMAIN` | Optional CloudFront/custom domain for media URLs |

Local dev uses **SQLite** when `DATABASE_URL` is unset. For PostgreSQL locally, set `POSTGRES_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, etc.

## Deploy on Render

The repo includes `render.yaml`. Render will:

1. Install Python and Node dependencies
2. Build the React app (`frontend/dist`)
3. Run `collectstatic` (admin assets only — `staticfiles/` is not committed)
4. Migrate and seed users on deploy
5. Start Gunicorn

Push to your connected Git branch; Render handles the rest.

See **[DEPLOY.md](DEPLOY.md)** for the full staging/production checklist (SMTP, Sentry, MFA verification).

### Staging environment

`render.yaml` defines a second **staging** web service (`human-resource-management-system-staging`) with its own PostgreSQL database. Use it to validate changes before production. Staging runs with `DEBUG=True` and the same security defaults (registration off, MFA enforced for admins).

## Health check

- `GET /api/v1/health/` — public endpoint returning `{ status, database, version }`
- Render uses this path for deploy health checks (`healthCheckPath` in `render.yaml`)

## API

- Base URL: `/api/v1/`
- Auth: session cookies + CSRF (see `POST /api/v1/auth/login/`)
- Interactive browse: log in via the SPA first, then visit `/api/v1/` in the same browser

## Useful commands

```powershell
python manage.py check
python manage.py test api
coverage run --source=api manage.py test api
coverage report --omit="api/tests/*"
python manage.py createsuperuser
python manage.py collectstatic --noinput
cd frontend && npm run build
```

## Security notes

- Public registration is **disabled by default**. Only admins can create users unless `ALLOW_PUBLIC_REGISTRATION=True`.
- Self-registration always assigns the **employee** role.
- **Admin MFA (TOTP)** is enforced on production (when `DATABASE_URL` is set). Locally it is **off by default** so you can log in immediately; use `.\start-backend.ps1` or set `ENFORCE_MFA_FOR_ADMINS=True` to test MFA at `/settings/security`.
- All API write operations (create/update/delete) are logged to the **audit trail** (viewable at `/audit-logs` in the SPA or `/api/v1/audit-logs/`).
- Leave, expense, performance appraisal, discipline appeal, recruitment, and benefit enrollment flows send **templated email notifications** when SMTP is configured.
- CI enforces **≥60% API test coverage** (see `.coveragerc`).
- Optional **Sentry** integration via `SENTRY_DSN`.

## Phase 2 features (workflow & policy depth)

- **Multi-step approval chains** for leave, expenses, and recruitment (`/api/v1/approval-workflows/`, `/api/v1/approval-requests/`)
- **In-app notification center** (bell icon in the top bar; `/api/v1/notifications/`)
- **Document management** — contracts, policies, offer letters (`/documents` in the SPA)
- **Leave policy sync** — `POST /api/v1/leave-policy-allocations/sync/` applies policies to employee balances
- **Report export** — CSV/Excel via `?format=xlsx` or the Export Excel button on Reports

Default workflows (seeded via `python manage.py seed_workflows`):

| Workflow | Steps |
|----------|-------|
| Leave | Manager → HR (HR step when duration ≥ 5 days) |
| Expense | Manager → HR (HR step when amount ≥ 10,000) |
| Recruitment | Manager → HR |

## Phase 3 features (enterprise integrations)

- **Google / Microsoft SSO** — OAuth2 login buttons on the sign-in page when credentials are configured (`/api/v1/auth/sso/`)
- **API keys** — machine-to-machine access via `Authorization: Api-Key <key>` (admin UI at `/settings/integrations`)
- **Webhooks** — outbound HTTP notifications for leave, expense, and employee lifecycle events
- **S3 media storage** — enable by setting `AWS_STORAGE_BUCKET_NAME` (uses `django-storages` + `boto3`)
- **Payroll export** — CSV/Excel/JSON at `GET /api/v1/payroll/export/?month=&year=&format=` (Export Excel on Reports → Payroll)
- **Org chart** — department hierarchy with parent/child relationships (`/org-chart`)
- **Role-based dashboards** — tailored views for employees, managers, and HR/admins on `/dashboard`

### Executive dashboard (C-suite / HR)

- **Executive command center** — hero KPIs with month-over-month deltas (headcount, joiners, payroll)
- **Attention banner** — urgent approvals, leave backlog, expenses, expiring certifications
- **Executive summary brief** — auto-generated narrative for leadership reviews
- **12-month trend charts** — workforce headcount and payroll outflow (Recharts area charts)
- **Hiring pipeline funnel** — received → shortlisted → interviewed → hired
- **Leave utilisation trend** — approved leave days over 6 months
- **PDF export** — “Export PDF” button (browser print-to-PDF, landscape A4)

## Phase 4 features (compliance & data governance)

- **GDPR subject access export** — employees download their data at `/settings/security`; admins export from employee profiles or `GET /api/v1/compliance/data-export/employees/{id}/`
- **Right to erasure** — admins anonymize employee PII via `/settings/compliance` (`POST /api/v1/compliance/erasure/{id}/`)
- **Audit log export** — CSV/Excel from the Audit Log page or `GET /api/v1/audit-logs/export/?format=csv|xlsx`
- **Data retention policies** — configurable retention for audit logs, webhook deliveries, and notifications at `/settings/compliance`
- **Scheduled purge** — `python manage.py apply_retention_policies` (add `--dry-run` to preview)

Default retention (seeded on migrate):

| Category | Default retention |
|----------|-------------------|
| Audit logs | 730 days (2 years) |
| Webhook deliveries | 90 days |
| Notifications | 180 days |

## Notes

- User uploads (resumes, receipts) are stored in `media/` (gitignored).
- `staticfiles/` is generated by `collectstatic` and should not be committed.
- Django admin remains at `/admin/`.

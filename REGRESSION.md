# Pre-release regression checklist

Minimal **functional + integration** suite to re-run before a release (this *is* your non-regression pack). Prefer a green CI run on `main`; use this when verifying locally or after a hotfixed deploy.

## 1. Prerequisites

```powershell
# From repo root, with venv active
python manage.py migrate
python manage.py seed_data --reset-password

cd frontend
npm ci
npx playwright install chromium
cd ..
```

Local defaults: `admin` / `Admin@HRMIS2026!`, `manager` / `Manager@HRMIS2026!`, `employee` / `Employee@HRMIS2026!`.

For E2E against Vite + API (typical local):

- Terminal A: `python manage.py runserver 127.0.0.1:8000`
- Terminal B: `cd frontend; npm run dev` (port `5173`)
- Optional MFA E2E: `python manage.py prepare_e2e_mfa` when those specs need a fixed TOTP secret

## 2. Automated gate (required)

Run in order; stop on first failure.

| Step | Command | Covers |
|------|---------|--------|
| Django system check | `python manage.py check` | Config / URLs |
| API functional + integration | `python manage.py test api` | Auth, RBAC, leave, payroll, reports, ops, MFA, … |
| Frontend unit | `cd frontend; npm test` | Client helpers / permissions |
| Frontend build | `cd frontend; npm run build` | Production bundle |
| E2E critical paths | `cd frontend; npm run e2e` | UI workflows (see below) |

PowerShell one-liner style:

```powershell
python manage.py check
python manage.py test api
cd frontend; npm test; npm run build; npm run e2e; cd ..
```

CI equivalent: push/PR green on `.github/workflows/ci.yml` (backend SQLite+Postgres, frontend Vitest+build, Playwright).

## 3. E2E paths that must stay green

These specs are the release **smoke regression** set:

| Spec | Business risk |
|------|----------------|
| `e2e/auth.spec.js` | Login / session |
| `e2e/mfa.spec.js` | Admin MFA |
| `e2e/leave-workflow.spec.js` | Submit + approve leave |
| `e2e/approvals.spec.js` | Approvals inbox |
| `e2e/payroll.spec.js` | Payroll visibility / actions |
| `e2e/reports.spec.js` | Reports overview + filters |
| `e2e/mobile-clock.spec.js` | Mobile punch |
| `e2e/smoke.spec.js` | Broad navigation smoke |

Run a subset when debugging:

```powershell
cd frontend
npx playwright test e2e/auth.spec.js e2e/leave-workflow.spec.js e2e/payroll.spec.js
```

If Playwright says the browser executable is missing: `npx playwright install chromium`.

## 4. Manual smoke (5–10 minutes, after deploy)

Log in as **admin** on the target environment:

- [ ] `/api/v1/health/` returns OK  
- [ ] Dashboard loads  
- [ ] Employees list opens  
- [ ] Create or open a leave request; approve from Approvals (or confirm pending appears)  
- [ ] Payroll page loads for an admin/manager with payroll access  
- [ ] Reports → Overview shows employee/attendance cards  
- [ ] Settings → Ops (if used) loads without error  
- [ ] Logout works  

Optional: clock-in once at `/mobile`.

## 5. Optional before a major release

```powershell
# Longer API confidence
coverage run --source=api manage.py test api
coverage report --omit="api/tests/*"

# Load smoke (Django must be up)
pip install locust
locust -f loadtest/locustfile.py --host http://127.0.0.1:8000 --headless -u 5 -r 2 -t 30s --only-summary
```

## Pass / fail

**Ship only if:** automated gate is green **and** manual smoke on the target URL succeeds.

**Do not ship if:** any `api` test fails, Playwright critical specs fail, or health/dashboard/login is broken in manual smoke.

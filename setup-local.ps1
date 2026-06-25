# One-time (or repeat) local setup: migrations, demo users, approval workflows.
# Run from project root: .\setup-local.ps1

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot 'hrmis_env\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    Write-Host 'Virtual env not found. Create it first:' -ForegroundColor Yellow
    Write-Host '  python -m venv hrmis_env'
    Write-Host '  .\hrmis_env\Scripts\activate'
    Write-Host '  pip install -r requirements.txt'
    exit 1
}

$env:DEBUG = 'True'
$env:ENFORCE_MFA_FOR_ADMINS = 'False'

Write-Host 'Running migrations...' -ForegroundColor Cyan
& $Python (Join-Path $ProjectRoot 'manage.py') migrate

Write-Host 'Seeding users and sample data...' -ForegroundColor Cyan
& $Python (Join-Path $ProjectRoot 'manage.py') seed_data --reset-password

Write-Host 'Seeding approval workflows...' -ForegroundColor Cyan
& $Python (Join-Path $ProjectRoot 'manage.py') seed_workflows

Write-Host ''
Write-Host 'Local setup complete.' -ForegroundColor Green
Write-Host 'Start backend:  .\hrmis_env\Scripts\python.exe manage.py runserver'
Write-Host 'Start frontend: cd frontend; npm run dev'
Write-Host 'Open http://localhost:5173'
Write-Host 'Login: admin / Admin@HRMIS2026!  (MFA optional locally; enable at /settings/security to test)'

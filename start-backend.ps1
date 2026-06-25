# Start Django dev server (port 8000). Run in one terminal while frontend uses npm run dev.
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot 'hrmis_env\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    Write-Host 'Run .\setup-local.ps1 first (or create hrmis_env).' -ForegroundColor Red
    exit 1
}

$env:DEBUG = 'True'
$env:ENFORCE_MFA_FOR_ADMINS = 'False'
Set-Location $ProjectRoot
& $Python manage.py runserver

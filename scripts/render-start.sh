#!/usr/bin/env bash
# Free-tier safe: Pre-Deploy Command is locked on Render free plans.
# Migrate + seed run here on every start (idempotent).
set -euo pipefail

python manage.py migrate --noinput
python manage.py seed_production --confirm

exec gunicorn avvento_hrmis.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --threads 2 \
  --timeout 120

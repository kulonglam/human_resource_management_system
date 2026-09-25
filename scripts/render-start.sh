#!/usr/bin/env bash
# Free-tier safe: Pre-Deploy Command is locked on Render free plans.
# Migrate + seed run here on every start (idempotent).
set -euo pipefail

python manage.py migrate --noinput

seed_args=(--confirm)
# Staging previously used seed_production --confirm --with-users. Keep that
# behavior when this is the staging service or the env flag is set.
if [ "${RENDER_SERVICE_NAME:-}" = "staging" ] || [ "${SEED_PRODUCTION_WITH_USERS:-}" = "1" ]; then
  seed_args+=(--with-users)
fi
python manage.py seed_production "${seed_args[@]}"

exec gunicorn avvento_hrmis.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --threads 2 \
  --timeout 120

#!/usr/bin/env bash
# Run on Render shell or any production host after env vars are configured.
# Requires: DATABASE_URL, SECRET_KEY, SEED_ADMIN_PASSWORD (and SEED_*_PASSWORD if --with-users).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python manage.py migrate --noinput
python manage.py seed_production --confirm "$@"

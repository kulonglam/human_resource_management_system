#!/usr/bin/env bash
set -euo pipefail

python --version

pip install -r requirements.txt

cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
npm run build
cd ..

python manage.py collectstatic --noinput

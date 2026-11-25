#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

case "${DEMO_SEED:-0}" in
    0) ;;
    1) python manage.py seed_demo --force ;;
    *) echo "DEMO_SEED must be 0 or 1." >&2; exit 2 ;;
esac

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-10000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --threads "${GUNICORN_THREADS:-2}"

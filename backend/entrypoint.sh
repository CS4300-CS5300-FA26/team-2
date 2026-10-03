#!/bin/sh
set -e

until python manage.py migrate --check >/dev/null 2>&1 || python manage.py migrate; do
  echo "Waiting for database..."
  sleep 1
done

python manage.py collectstatic --noinput

exec gunicorn pathfinder.wsgi:application --bind 0.0.0.0:8000

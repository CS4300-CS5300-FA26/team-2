#!/bin/sh
# Azure App Service startup command: `sh startup.sh`. Migrate, collect static, serve.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn pathfinder.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120

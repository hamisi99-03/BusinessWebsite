#!/usr/bin/env bash
set -o errexit
python manage.py migrate --no-input
gunicorn ecommerce_manager.wsgi:application \
  --workers 2 \
  --threads 4 \
  --worker-class gthread \
  --worker-tmp-dir /dev/shm \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 50

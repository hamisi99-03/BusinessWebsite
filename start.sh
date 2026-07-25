#!/usr/bin/env bash
set -o errexit
python manage.py migrate --no-input
gunicorn ecommerce_manager.wsgi:application

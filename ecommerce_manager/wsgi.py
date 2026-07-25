"""
WSGI config for ecommerce_manager project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_manager.settings')

# Run migrations before handling any requests
import django
django.setup()

from django.core.management import call_command
from django.db import connection

try:
    # Check if the database needs migrations by trying a simple query
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
except Exception:
    pass  # Database might not exist yet, let migrate handle it

try:
    call_command('migrate', '--no-input', verbosity=1)
    logging.warning('Migrations completed successfully on startup')
except Exception as e:
    logging.error('Migration failed on startup: %s', e)
    raise

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

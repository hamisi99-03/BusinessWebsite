"""
WSGI config for ecommerce_manager project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import subprocess
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_manager.settings')

import django
from django.conf import settings

django.setup()

db = settings.DATABASES['default']
logging.warning('Database engine: %s', db['ENGINE'])

# Run migrations via subprocess — most reliable method
logging.warning('Running migrations...')
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', '--no-input'],
    capture_output=True, text=True, cwd=settings.BASE_DIR
)
logging.warning('Migration stdout: %s', result.stdout)
if result.stderr:
    logging.warning('Migration stderr: %s', result.stderr)
if result.returncode != 0:
    logging.error('Migration failed with code %d', result.returncode)
    raise RuntimeError(f'Migration failed: {result.stderr}')
logging.warning('Migrations completed successfully')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

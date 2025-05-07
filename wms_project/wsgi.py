"""
WSGI config for wms_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')

# --- Run migrations automatically on startup ---
import django
django.setup()
from django.core.management import call_command

try:
    call_command('migrate', interactive=False)
except Exception as e:
    print("Migration error during WSGI startup:", e)
# ------------------------------------------------

application = get_wsgi_application()

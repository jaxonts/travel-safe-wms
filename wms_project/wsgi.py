import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms_project.settings')

application = get_wsgi_application()

# Automatically run migrations at startup on Render
try:
    from django.core.management import call_command
    call_command("migrate", interactive=False)
except Exception as e:
    print(f"Migration error: {e}")

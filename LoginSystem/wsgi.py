"""WSGI entry point for the Login System project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LoginSystem.settings")
application = get_wsgi_application()

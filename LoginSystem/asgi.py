"""ASGI entry point for the Login System project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LoginSystem.settings")
application = get_asgi_application()

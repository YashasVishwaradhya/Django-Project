"""Project URL configuration."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Keep Django admin at its usual URL and send the rest to Loginify.
    path("admin/", admin.site.urls),
    path("", include("Loginify.urls")),
]

"""Application routes for pages and the staff-only JSON API."""
from django.urls import path

from . import views

urlpatterns = [
    # Signup and login pages, plus the small hello endpoint.
    path("hello/", views.hello_world, name="hello"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("success/", views.success, name="success"),
    # Staff-only JSON endpoints for profile CRUD.
    path("api/users/", views.get_all_user_details, name="api-users"),
    path("api/users/<str:email>/", views.get_user_by_email, name="api-user-detail"),
    path(
        "api/users/<str:email>/update/",
        views.update_user_details,
        name="api-user-update",
    ),
    path(
        "api/users/<str:email>/delete/",
        views.delete_user_by_email,
        name="api-user-delete",
    ),
]

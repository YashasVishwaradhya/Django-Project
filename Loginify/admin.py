from django.contrib import admin

from .models import UserDetails


@admin.register(UserDetails)
class UserDetailsAdmin(admin.ModelAdmin):
    # Show searchable profile fields, but hide the unused password field.
    list_display = ("username", "email", "related_user")
    search_fields = ("username", "email", "related_user__username")
    exclude = ("password",)

"""Profile details required by the assignment."""
from django.conf import settings
from django.db import models


class UserDetails(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    email = models.EmailField(unique=True)
    # Kept for the assignment schema; Django auth stores the real password hash.
    password = models.CharField(max_length=12, blank=True)
    # Link this profile to the Django account that handles login securely.
    related_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    def __str__(self):
        return self.username

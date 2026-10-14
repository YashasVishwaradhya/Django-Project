# Initial profile migration.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="UserDetails",
            fields=[
                ("username", models.CharField(max_length=50, primary_key=True, serialize=False)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(blank=True, max_length=12)),
                (
                    "related_user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

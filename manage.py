#!/usr/bin/env python
"""Command-line utility for the Login System project."""
import os
import sys


def main():
    # Tell Django which settings file this project uses.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LoginSystem.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not installed. Activate the DjangoAssignment environment "
            "and install requirements.txt first."
        ) from exc
    # Pass commands such as runserver and migrate to Django.
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

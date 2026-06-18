"""Idempotently seed the single dev owner (T-020).

    python manage.py seed_dev_owner

Dev-only: discoverable only when DEBUG (the app is registered under DEBUG). Prints
the credentials and the login shortcut so a developer can authenticate via the
browser (``/dev/login/``) or ``manage.py shell``.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from devtools.owner import get_or_create_dev_owner


class Command(BaseCommand):
    help = "Create (idempotently) the local dev owner user."

    def handle(self, *args, **opts):
        user, created = get_or_create_dev_owner()
        verb = "created" if created else "already exists"
        self.stdout.write(
            f"dev owner {verb}: username={user.username} "
            f"password={settings.DEV_OWNER_PASSWORD} -> visit /dev/login/"
        )

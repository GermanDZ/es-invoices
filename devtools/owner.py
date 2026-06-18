"""Get-or-create the single dev owner (T-020).

Dev-only: never imported in production because the ``devtools`` app is registered
in INSTALLED_APPS only under DEBUG. ``scope.md`` D-3 fixes the account model as
single-operator, so there is exactly one owner to seed.
"""
from django.conf import settings
from django.contrib.auth import get_user_model


def get_or_create_dev_owner():
    """Idempotently return the seeded dev owner.

    Creates it with the configured dev password on first call; subsequent calls
    return the existing user untouched. Returns ``(user, created)``.
    """
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=settings.DEV_OWNER_USERNAME
    )
    if created:
        user.set_password(settings.DEV_OWNER_PASSWORD)
        user.save(update_fields=["password"])
    return user, created

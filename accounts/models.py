"""Account-lifecycle models for T-028 automated data retention.

:class:`DeletionRequest` records the timestamp at which a user requested their
account to be deleted. The ``purge_expired_data`` management command uses this
to implement the 30-day grace period (RGPD Art. 17, rgpd-checklist.md §5):

* When ``requested_at`` is older than 30 days the account and all its associated
  data (invoices, clients, certificates) are hard-deleted via the normal Django
  ``User.delete()`` cascade.
* The record is separate from ``auth.User`` so the 30-day window survives partial
  session state and the operator can inspect pending requests without fetching
  user objects.
"""
from django.conf import settings
from django.db import models


class DeletionRequest(models.Model):
    """Tracks a user's explicit request to delete their account.

    One-to-one with ``auth.User``; the cascade mirrors ``User.delete()`` so there
    is never an orphan deletion request after a purge. The ``requested_at``
    timestamp is set once at creation and never updated — the single source of
    truth for the 30-day countdown.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deletion_request",
    )
    requested_at = models.DateTimeField(
        help_text="When the user requested account deletion (UTC)."
    )

    def __str__(self) -> str:
        return f"DeletionRequest for {self.user_id} at {self.requested_at:%Y-%m-%d}"

"""Management command: purge_expired_data — RGPD Art. 17 automated deletion.

Enforces the retention policy from docs/rgpd-checklist.md §5 (T-028).

Two categories are purged:

1. **Fiscal records** — Invoices (and their line items, Verifactu records, and
   submission attempts) whose ``issue_date`` is older than the configured
   retention window (default 5 years).  Clients are also purged when *every*
   invoice they appear on has expired.  ``Series`` objects are left intact; they
   carry no personal data and their ``last_number`` counter is a legal audit trail.

2. **User accounts** — Accounts with an active :class:`accounts.DeletionRequest`
   whose ``requested_at`` is older than the grace period (default 30 days).
   Django's cascade removes the user's invoices, clients, certificates, and
   submission records automatically.

Both categories are idempotent — running the command multiple times in a row
produces the same outcome as running it once (no phantom deletions on the second
run).

``--dry-run``  prints what *would* be deleted without performing any writes.
"""
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import DeletionRequest
from invoicing.models import Invoice

logger = logging.getLogger(__name__)

User = get_user_model()

# Default retention constants (operator can override via command arguments).
_INVOICE_RETENTION_YEARS = 5
_ACCOUNT_GRACE_DAYS = 30


class Command(BaseCommand):
    help = (
        "Purge personal data that has exceeded its retention window "
        "(RGPD Art. 17, rgpd-checklist.md §5). "
        "Deletes expired invoices/clients and accounts past their grace period."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Log what would be deleted without performing any writes.",
        )
        parser.add_argument(
            "--invoice-retention-years",
            type=int,
            default=_INVOICE_RETENTION_YEARS,
            metavar="YEARS",
            help=(
                f"Retention window for invoice records (default: {_INVOICE_RETENTION_YEARS} years). "
                "Invoices issued before NOW - YEARS will be deleted."
            ),
        )
        parser.add_argument(
            "--account-grace-days",
            type=int,
            default=_ACCOUNT_GRACE_DAYS,
            metavar="DAYS",
            help=(
                f"Grace period after a deletion request before the account is purged "
                f"(default: {_ACCOUNT_GRACE_DAYS} days)."
            ),
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        invoice_retention_years: int = options["invoice_retention_years"]
        account_grace_days: int = options["account_grace_days"]

        mode = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.NOTICE(
                f"{mode}purge_expired_data starting "
                f"(invoice_retention={invoice_retention_years}y, "
                f"account_grace={account_grace_days}d)"
            )
        )

        now = timezone.now()
        invoice_cutoff = (now - timedelta(days=invoice_retention_years * 365)).date()
        account_cutoff = now - timedelta(days=account_grace_days)

        invoices_deleted = self._purge_expired_invoices(
            invoice_cutoff, dry_run=dry_run
        )
        clients_deleted = self._purge_orphaned_clients(dry_run=dry_run)
        accounts_deleted = self._purge_requested_accounts(
            account_cutoff, dry_run=dry_run
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}Done — invoices deleted: {invoices_deleted}, "
                f"clients deleted: {clients_deleted}, "
                f"accounts deleted: {accounts_deleted}."
            )
        )

    # ------------------------------------------------------------------
    # Invoice purge
    # ------------------------------------------------------------------

    def _purge_expired_invoices(self, cutoff_date, *, dry_run: bool) -> int:
        """Delete issued invoices whose issue_date is before cutoff_date.

        Cascade in the DB removes LineItems, VerifactuRecords (compliance), and
        SubmissionAttempts.  Draft invoices (``issued=False``) carry no legal
        fiscal record and are excluded from retention accounting — they should be
        cleaned up separately if needed.
        """
        qs = Invoice.objects.filter(issued=True, issue_date__lt=cutoff_date)
        count = qs.count()
        if count == 0:
            logger.info("No expired invoices found (cutoff %s).", cutoff_date)
            return 0

        logger.info(
            "%sPurging %d invoices issued before %s.",
            "[DRY RUN] " if dry_run else "",
            count,
            cutoff_date,
        )

        if not dry_run:
            with transaction.atomic():
                deleted, _ = qs.delete()
                logger.info("Deleted %d invoice rows (+ cascades).", deleted)

        return count

    # ------------------------------------------------------------------
    # Orphaned client purge
    # ------------------------------------------------------------------

    def _purge_orphaned_clients(self, *, dry_run: bool) -> int:
        """Delete clients whose every associated invoice has been purged.

        A ``Client`` is considered orphaned when it has no remaining ``Invoice``
        objects (the FK set is empty after the invoice purge above).  Clients
        with at least one surviving invoice are retained — their personal data is
        still tied to a live fiscal record.
        """
        from clients.models import Client

        # clients that have no invoices left at all
        qs = Client.objects.filter(invoices__isnull=True)
        count = qs.count()
        if count == 0:
            logger.info("No orphaned clients to purge.")
            return 0

        logger.info(
            "%sPurging %d orphaned clients.",
            "[DRY RUN] " if dry_run else "",
            count,
        )

        if not dry_run:
            with transaction.atomic():
                deleted, _ = qs.delete()
                logger.info("Deleted %d client rows.", deleted)

        return count

    # ------------------------------------------------------------------
    # Account purge
    # ------------------------------------------------------------------

    def _purge_requested_accounts(self, cutoff_dt, *, dry_run: bool) -> int:
        """Delete user accounts whose DeletionRequest is older than cutoff_dt.

        Django's cascade removes invoices, clients, certificates, and submission
        records tied to the user.  Only accounts that have explicitly opted in
        via a :class:`~accounts.models.DeletionRequest` are eligible — accounts
        with no request (active users) are never touched.
        """
        expired_requests = DeletionRequest.objects.filter(
            requested_at__lt=cutoff_dt
        ).select_related("user")

        count = expired_requests.count()
        if count == 0:
            logger.info(
                "No deletion-requested accounts past the grace period (cutoff %s).",
                cutoff_dt,
            )
            return 0

        logger.info(
            "%sPurging %d accounts past the deletion grace period.",
            "[DRY RUN] " if dry_run else "",
            count,
        )

        if not dry_run:
            with transaction.atomic():
                # Collect PKs first to avoid evaluate-after-delete issues.
                user_pks = list(expired_requests.values_list("user_id", flat=True))
                # Invoice.series uses on_delete=PROTECT, so Django's User cascade
                # cannot delete Series (and therefore the User) while invoices exist.
                # Purge all invoices belonging to the user's series first.
                Invoice.objects.filter(series__owner_id__in=user_pks).delete()
                deleted_count, _ = User.objects.filter(pk__in=user_pks).delete()
                logger.info(
                    "Deleted %d user rows (+ cascades).", deleted_count
                )

        return count

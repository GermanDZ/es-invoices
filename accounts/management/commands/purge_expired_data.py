"""Management command: purge_expired_data — RGPD Art. 17 automated deletion.

Enforces the retention policy from docs/rgpd-checklist.md §5 (T-028).

Two categories are purged:

1. **Fiscal records** — Issued invoices (and their line items, Verifactu records,
   and submission attempts) whose ``issue_date`` is older than the configured
   retention window (default 5 years).  Clients are purged only when they were
   linked to invoices that were actually deleted in the same purge run — this
   avoids destroying clients that simply have no invoices yet.

2. **User accounts** — Accounts with an active :class:`accounts.DeletionRequest`
   whose ``requested_at`` is older than the grace period (default 30 days) **and**
   whose invoices are all past the 5-year retention window.  If a user has any
   invoice still within the retention window the account is skipped (the
   DeletionRequest is left in place; no personal data is removed) — preserving
   Spanish fiscal retention obligations (Ley 58/2003 General Tributaria).
   When all a user's invoices have aged out the user row (and their Series +
   Certificates) is deleted via Django's cascade.

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

        invoices_deleted, purged_client_ids = self._purge_expired_invoices(
            invoice_cutoff, dry_run=dry_run
        )
        clients_deleted = self._purge_orphaned_clients(
            purged_client_ids, dry_run=dry_run
        )
        accounts_deleted, accounts_skipped = self._purge_requested_accounts(
            account_cutoff, invoice_cutoff, dry_run=dry_run
        )

        if accounts_skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"{mode}Skipped {accounts_skipped} account(s) with deletion "
                    "requests that still have invoices within the retention window "
                    "(fiscal retention obligation — will retry once invoices age out)."
                )
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

    def _purge_expired_invoices(
        self, cutoff_date, *, dry_run: bool
    ) -> tuple[int, set]:
        """Delete issued invoices whose issue_date is before cutoff_date.

        Cascade in the DB removes LineItems, VerifactuRecords (compliance), and
        SubmissionAttempts.  Draft invoices (``issued=False``) carry no legal
        fiscal record and are excluded from retention accounting — they should be
        cleaned up separately if needed.

        Returns ``(count, client_id_set)`` where ``client_id_set`` is the set of
        ``client_id`` values from the deleted invoices — used by
        :meth:`_purge_orphaned_clients` so it only checks clients that were
        actually referenced by deleted invoices, not all clients with no invoices.
        """
        qs = Invoice.objects.filter(issued=True, issue_date__lt=cutoff_date)
        count = qs.count()
        if count == 0:
            logger.info("No expired invoices found (cutoff %s).", cutoff_date)
            return 0, set()

        # Collect referenced client IDs *before* deletion.
        client_ids: set = set(
            qs.exclude(client__isnull=True).values_list("client_id", flat=True)
        )

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

        return count, client_ids

    # ------------------------------------------------------------------
    # Orphaned client purge
    # ------------------------------------------------------------------

    def _purge_orphaned_clients(
        self, purged_client_ids: set, *, dry_run: bool
    ) -> int:
        """Delete clients that were linked to deleted invoices and now have none.

        Only clients whose IDs appear in ``purged_client_ids`` (the set returned
        by :meth:`_purge_expired_invoices`) are candidates — this avoids deleting
        clients that simply have not been invoiced yet, or clients whose invoices
        are still within the retention window.

        A candidate client is deleted only if it has **no remaining invoices**
        after the expired ones were removed.
        """
        if not purged_client_ids:
            logger.info("No purged invoices had client links — skipping client purge.")
            return 0

        from clients.models import Client

        # Among the referenced clients, keep only those with no surviving invoices.
        qs = Client.objects.filter(
            pk__in=purged_client_ids, invoices__isnull=True
        )
        count = qs.count()
        if count == 0:
            logger.info("No orphaned clients to purge (all had surviving invoices).")
            return 0

        logger.info(
            "%sPurging %d orphaned clients (previously linked to expired invoices).",
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

    def _purge_requested_accounts(
        self, cutoff_dt, invoice_cutoff_date, *, dry_run: bool
    ) -> tuple[int, int]:
        """Delete user accounts whose DeletionRequest is older than cutoff_dt.

        Only purges accounts **all of whose invoices** are also past the
        ``invoice_cutoff_date`` — preserving Spanish fiscal retention obligations
        (Ley 58/2003 General Tributaria, 5-year invoice retention). Accounts with
        any invoice still within the retention window are skipped and logged;
        the DeletionRequest is left in place for the next purge run.

        For accounts that ARE eligible: invoices are deleted first (to avoid the
        ``Invoice.series`` PROTECT constraint), then the User row is deleted via
        Django's cascade which removes Series, Certificates, and DeletionRequest.

        Returns ``(deleted_count, skipped_count)``.
        """
        expired_requests = DeletionRequest.objects.filter(
            requested_at__lt=cutoff_dt
        ).select_related("user")

        total = expired_requests.count()
        if total == 0:
            logger.info(
                "No deletion-requested accounts past the grace period (cutoff %s).",
                cutoff_dt,
            )
            return 0, 0

        # Split eligible (all invoices aged out) from blocked (recent invoices).
        eligible_pks: list[int] = []
        skipped_pks: list[int] = []

        for req in expired_requests:
            user_id = req.user_id
            has_recent = Invoice.objects.filter(
                series__owner_id=user_id,
                issued=True,
                issue_date__gte=invoice_cutoff_date,
            ).exists()
            if has_recent:
                skipped_pks.append(user_id)
            else:
                eligible_pks.append(user_id)

        if skipped_pks:
            logger.warning(
                "Skipping %d account(s) — still have invoices within retention window: %s",
                len(skipped_pks),
                skipped_pks,
            )

        if not eligible_pks:
            return 0, len(skipped_pks)

        logger.info(
            "%sPurging %d account(s) past grace period with no recent invoices.",
            "[DRY RUN] " if dry_run else "",
            len(eligible_pks),
        )

        if not dry_run:
            with transaction.atomic():
                # Delete invoices first to clear the Invoice.series PROTECT FK.
                Invoice.objects.filter(
                    series__owner_id__in=eligible_pks
                ).delete()
                # Delete the user rows; Django cascade removes Series +
                # DeletionRequest + Certificates.
                deleted_count, _ = User.objects.filter(
                    pk__in=eligible_pks
                ).delete()
                logger.info("Deleted %d user rows (+ cascades).", deleted_count)

        return len(eligible_pks), len(skipped_pks)

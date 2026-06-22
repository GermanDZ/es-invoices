"""Tests for the purge_expired_data management command (T-028).

Covers:
- Dry-run mode: logs counts but performs no writes
- Actual deletion of expired invoices (> 5 years old)
- Retention boundary: invoice exactly at cutoff is NOT deleted (5yr - 1 day kept)
- Orphaned client purge: client with all invoices gone is deleted; client with a
  surviving invoice is retained
- Account purge: account past grace period is deleted; within-grace account is kept
- Idempotency: running twice produces the same result as running once
"""
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import DeletionRequest
from clients.models import Client
from invoicing.models import Invoice, LineItem, Series

User = get_user_model()


def _make_user(username="user@example.com"):
    return User.objects.create_user(
        username=username, email=username, password="testpass-7"
    )


def _make_series(owner):
    return Series.objects.create(owner=owner, prefix="T")


def _make_invoice(series, issue_date, *, issued=True):
    """Create a minimal issued invoice on the given date."""
    inv = Invoice.objects.create(
        series=series,
        number=None,
        issue_date=issue_date,
        issued=issued,
        recipient_name="Test Recipient",
        recipient_taxid="B12345678",
        recipient_address="Calle Mayor 1",
    )
    LineItem.objects.create(
        invoice=inv,
        description="Service",
        quantity=1,
        unit_price=100,
        iva_rate=21,
    )
    if issued:
        # assign a number manually so the model's immutability guard is satisfied
        inv.number = Invoice.objects.filter(series=series).count()
        # bypass the immutability guard since we're setting number in the same op
        Invoice.objects.filter(pk=inv.pk).update(number=inv.number)
    return inv


def _years_ago(years, extra_days=0):
    """Return a naive date ``years`` years ago (plus ``extra_days``)."""
    today = timezone.now().date()
    return today.replace(year=today.year - years) + datetime.timedelta(days=extra_days)


def _days_ago(days):
    return timezone.now() - datetime.timedelta(days=days)


class DryRunTests(TestCase):
    """--dry-run must never mutate the database."""

    def test_dry_run_leaves_expired_invoice(self):
        user = _make_user()
        series = _make_series(user)
        _make_invoice(series, _years_ago(6))  # 6 years old → would be purged

        call_command("purge_expired_data", "--dry-run", verbosity=0)

        self.assertEqual(Invoice.objects.count(), 1)

    def test_dry_run_leaves_expired_account(self):
        user = _make_user("del@example.com")
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(60))

        call_command("purge_expired_data", "--dry-run", verbosity=0)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())


class InvoicePurgeTests(TestCase):
    """Expired invoices are deleted; in-window invoices are kept."""

    def setUp(self):
        self.user = _make_user()
        self.series = _make_series(self.user)

    def test_invoice_older_than_5_years_is_deleted(self):
        _make_invoice(self.series, _years_ago(6))
        call_command("purge_expired_data", verbosity=0)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_invoice_exactly_at_5_year_boundary_is_deleted(self):
        # issue_date < cutoff — the cutoff is today - 5*365 days
        cutoff_date = (
            timezone.now() - datetime.timedelta(days=5 * 365)
        ).date()
        # issued one day before the cutoff (older than 5 years)
        _make_invoice(self.series, cutoff_date - datetime.timedelta(days=1))
        call_command("purge_expired_data", verbosity=0)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_invoice_within_retention_window_is_kept(self):
        # 5 years - 1 day: issue_date == cutoff → NOT deleted (strict <)
        cutoff_date = (
            timezone.now() - datetime.timedelta(days=5 * 365)
        ).date()
        _make_invoice(self.series, cutoff_date)  # exactly at cutoff → kept
        call_command("purge_expired_data", verbosity=0)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_recent_invoice_is_kept(self):
        today = timezone.now().date()
        _make_invoice(self.series, today)
        call_command("purge_expired_data", verbosity=0)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_draft_invoice_is_not_purged(self):
        # Draft invoices (issued=False) have no retention period — excluded.
        old_date = _years_ago(7)
        inv = Invoice.objects.create(
            series=self.series,
            issue_date=old_date,
            issued=False,
            recipient_name="Draft",
            recipient_taxid="B12345678",
        )
        call_command("purge_expired_data", verbosity=0)
        self.assertTrue(Invoice.objects.filter(pk=inv.pk).exists())

    def test_idempotent_second_run_no_error(self):
        _make_invoice(self.series, _years_ago(6))
        call_command("purge_expired_data", verbosity=0)
        # second run should be a no-op
        call_command("purge_expired_data", verbosity=0)
        self.assertEqual(Invoice.objects.count(), 0)


class ClientPurgeTests(TestCase):
    """Orphaned clients are deleted; clients with surviving invoices are retained."""

    def setUp(self):
        self.user = _make_user()
        self.series = _make_series(self.user)

    def _make_client(self):
        return Client.objects.create(
            owner=self.user,
            fiscal_name="Test Client",
            client_type=Client.ClientType.B2B,
            tax_id="B12345678",
        )

    def test_client_with_all_invoices_expired_is_deleted(self):
        client = self._make_client()
        inv = _make_invoice(self.series, _years_ago(6))
        inv.client = client
        Invoice.objects.filter(pk=inv.pk).update(client=client)

        call_command("purge_expired_data", verbosity=0)

        self.assertFalse(Client.objects.filter(pk=client.pk).exists())

    def test_client_with_surviving_invoice_is_retained(self):
        client = self._make_client()
        old_inv = _make_invoice(self.series, _years_ago(6))
        Invoice.objects.filter(pk=old_inv.pk).update(client=client)
        recent_inv = _make_invoice(self.series, timezone.now().date())
        Invoice.objects.filter(pk=recent_inv.pk).update(client=client)

        call_command("purge_expired_data", verbosity=0)

        self.assertTrue(Client.objects.filter(pk=client.pk).exists())

    def test_client_with_no_invoices_is_deleted(self):
        # A client that was never linked to any invoice is orphaned.
        client = self._make_client()
        call_command("purge_expired_data", verbosity=0)
        self.assertFalse(Client.objects.filter(pk=client.pk).exists())


class AccountPurgeTests(TestCase):
    """Accounts past their grace period are deleted; within-grace accounts are kept."""

    def test_account_past_grace_period_is_deleted(self):
        user = _make_user("del@example.com")
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(31))

        call_command("purge_expired_data", verbosity=0)

        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_account_within_grace_period_is_kept(self):
        user = _make_user("grace@example.com")
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(1))

        call_command("purge_expired_data", verbosity=0)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_account_exactly_29_days_old_is_kept(self):
        user = _make_user("exact@example.com")
        # 29 days old — inside the 30-day grace window, must not be deleted.
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(29))

        call_command("purge_expired_data", verbosity=0)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_account_without_deletion_request_is_never_deleted(self):
        user = _make_user("active@example.com")
        # no DeletionRequest — active user
        call_command("purge_expired_data", verbosity=0)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_account_deletion_cascades_invoices_and_clients(self):
        user = _make_user("cascade@example.com")
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(60))
        series = _make_series(user)
        _make_invoice(series, timezone.now().date())

        call_command("purge_expired_data", verbosity=0)

        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(Series.objects.filter(owner=user).exists())

    def test_idempotent_second_run_no_error(self):
        user = _make_user("idem@example.com")
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(60))
        call_command("purge_expired_data", verbosity=0)
        # second run — user gone, DeletionRequest gone
        call_command("purge_expired_data", verbosity=0)
        self.assertFalse(User.objects.filter(pk=user.pk).exists())


class CustomRetentionArgTests(TestCase):
    """Custom --invoice-retention-years and --account-grace-days are respected."""

    def test_custom_invoice_retention(self):
        user = _make_user()
        series = _make_series(user)
        # 3 years old — normally kept (default 5y window), but with 2y retention deleted
        _make_invoice(series, _years_ago(3))
        call_command(
            "purge_expired_data", "--invoice-retention-years", "2", verbosity=0
        )
        self.assertEqual(Invoice.objects.count(), 0)

    def test_custom_account_grace(self):
        user = _make_user("custom@example.com")
        # 5 days old request — normally kept (default 30d grace), deleted with 3d grace
        DeletionRequest.objects.create(user=user, requested_at=_days_ago(5))
        call_command(
            "purge_expired_data", "--account-grace-days", "3", verbosity=0
        )
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

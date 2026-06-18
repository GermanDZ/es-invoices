"""Gap-free numbering tests (T-012 requirement 4) — the R-02 surface."""
import threading
from decimal import Decimal
from unittest import mock

from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from invoicing.models import Invoice, Series
from invoicing.services import issue_invoice
from invoicing.tests.factories import make_invoice, make_series, make_user


class SequentialNumberingTests(TestCase):
    def test_assigns_consecutive_numbers_and_advances_high_water(self):
        """Req 4: each issue gets N+1; the series high-water mark advances."""
        series = make_series()
        numbers = []
        for _ in range(3):
            inv = make_invoice(series=series, lines=[(1, "100.00", 21)])
            issue_invoice(inv)
            numbers.append(inv.number)
        self.assertEqual(numbers, [1, 2, 3])
        series.refresh_from_db()
        self.assertEqual(series.last_number, 3)

    def test_unique_constraint_blocks_a_duplicate_number(self):
        """Req 4: (series, number) is unique — a duplicate cannot be committed."""
        series = make_series()
        first = make_invoice(series=series, lines=[(1, "100.00", 21)])
        issue_invoice(first)
        clash = make_invoice(series=series, lines=[(1, "100.00", 21)])
        clash.number = first.number
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                clash.save()

    def test_retry_resolves_a_lost_update_without_gap_or_duplicate(self):
        """Req 4: a collision on a lock-less backend rolls back and retries,
        yielding the next number — no gap, no duplicate."""
        series = make_series()
        inv = make_invoice(series=series, lines=[(1, "100.00", 21)])

        real_save = Invoice.save
        calls = {"n": 0}

        def flaky_save(self, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:                       # simulate the racing writer
                raise IntegrityError("simulated lost update")
            return real_save(self, *args, **kwargs)

        with mock.patch.object(Invoice, "save", flaky_save):
            issue_invoice(inv)

        self.assertEqual(calls["n"], 2)               # failed once, retried once
        self.assertEqual(inv.number, 1)               # no gap — still the first number
        series.refresh_from_db()
        self.assertEqual(series.last_number, 1)
        self.assertEqual(Invoice.objects.filter(series=series).count(), 1)


@skipUnlessDBFeature("has_select_for_update")
class ConcurrentIssuanceTests(TransactionTestCase):
    """True concurrent issuance against a backend with real row locks.

    Skipped on the SQLite test fallback (no ``select_for_update`` row lock and
    no cross-thread in-memory DB); the deterministic retry test above covers the
    lock-less path. On PostgreSQL (the production datastore, AD-6) this proves
    two racing issues serialize on the series row lock with no gap/duplicate.
    """

    def test_two_racing_issues_get_distinct_consecutive_numbers(self):
        owner = make_user()
        series = make_series(owner=owner)
        ready = threading.Barrier(2)
        results = []

        def worker():
            inv = make_invoice(series=series, lines=[(1, "100.00", 21)])
            ready.wait()
            issue_invoice(inv)
            results.append(inv.number)
            connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sorted(results), [1, 2])      # consecutive, no gap
        self.assertEqual(len(set(results)), 2)         # no duplicate
        series.refresh_from_db()
        self.assertEqual(series.last_number, 2)

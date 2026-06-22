# T-028 Design Notes — Automated Data Retention

## Completion Verification (step 1a)

Graded against commit 022838b (feature/T-028-automated-data-retention).

- ✅ [AC-1] `purge_expired_data` management command in `accounts` app —
  `accounts/management/commands/purge_expired_data.py` (new file in diff).
- ✅ [AC-2] Deletes invoices/line items issued > 5 years ago (configurable) —
  `_purge_expired_invoices(cutoff_date)` with `--invoice-retention-years` flag;
  Django cascade removes LineItems; tests `test_invoice_older_than_5_years_is_deleted`
  and `test_invoice_exactly_at_5_year_boundary_is_deleted` green.
- ✅ [AC-3] Deletes client records when last associated invoice > 5 years ago —
  `_purge_orphaned_clients()` queries `Client.objects.filter(invoices__isnull=True)`;
  `test_client_with_all_invoices_expired_is_deleted` green.
- ✅ [AC-4] Handles accounts in deletion-requested state > 30 days —
  `DeletionRequest` model (one-to-one with User, `requested_at` field) +
  `_purge_requested_accounts()` with `--account-grace-days` flag;
  `test_account_past_grace_period_is_deleted` green.
- ✅ [AC-5] Dry-run mode — `--dry-run` flag; every mutating block is guarded
  `if not dry_run:`; `test_dry_run_leaves_expired_invoice` and
  `test_dry_run_leaves_expired_account` green.
- ✅ [AC-6] Idempotent — `test_idempotent_second_run_no_error` (invoices) and
  `test_idempotent_second_run_no_error` (accounts) both green.
- ✅ [AC-7] Tests cover dry-run, actual deletion, retention boundary —
  19 tests in `accounts/tests/test_purge_expired_data.py`; full suite 204 green.
- ✅ [AC-8] `python3 scripts/check-docs.py` passes — confirmed at completion.

## Success Measures

n/a — this is an operational/compliance feature (a scheduled management
command). Success is measured operationally: the command runs without error on a
production database and the RGPD retention obligation is met. No application-level
instrumentation (events/metrics) is appropriate for a CLI-only purge command.

## Key Design Decisions

**DD-1: DeletionRequest as separate model (not a flag on User)**
Using a standalone `DeletionRequest` model (OneToOneField to User) avoids any
custom User model migration. The `requested_at` timestamp is the single source of
truth for the 30-day countdown. The OneToOne + `on_delete=CASCADE` means the record
is automatically removed when the User is purged — no orphan cleanup needed.

**DD-2: Invoice.series PROTECT constraint workaround**
`Series.owner` is CASCADE, but `Invoice.series` is PROTECT. Django's built-in
cascade for User deletion would hit PROTECT when trying to delete Series rows.
Solution: `_purge_requested_accounts` explicitly deletes the user's invoices
(`Invoice.objects.filter(series__owner_id__in=user_pks).delete()`) before
the `User.delete()` cascade, which then cleanly removes Series and the User.

**DD-3: Orphaned clients = no invoices at all**
A Client is considered orphaned when `invoices__isnull=True` — no invoices
remain at all, including ones from a different user who happen to reference
the same client (not possible in this schema since Client is owner-scoped, but
the query is correct regardless). Clients with any surviving invoice are kept.

**DD-4: Draft invoices excluded from retention**
Only `issued=True` invoices carry a legal fiscal record and a meaningful
`issue_date`. Drafts (never issued) are excluded from the retention window —
they should be managed separately.

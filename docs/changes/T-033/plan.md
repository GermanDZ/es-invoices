---
id: T-033
type: work-item
status: in-progress
priority: high
depends-on: [T-023, T-022]
touches:
  - invoicing/views.py
  - invoicing/services.py
  - invoicing/templates/invoicing/invoice_form.html
  - invoicing/tests/
  - docs/changes/T-033/
---

# T-033 — Wire generate_alta into invoice issuance

## Goal

When a user issues a regular invoice through the web form, a `VerifactuRecord` (`alta`)
is automatically generated at issue time. The invoice detail page then shows the
"Registrar / Enviar a la AEAT" submit button as active (not the "no record yet" message),
completing the actor path from invoice creation to AEAT submission.

## Context

`issue_invoice()` in `invoicing/services.py` assigns gap-free numbering and marks the
invoice `issued=True`, but does **not** call `compliance.generate_alta()`. The submission
view (`submission:submit`) guards on `latest_alta_record(invoice) is None` and returns the
"Esta factura aún no tiene un registro Verifactu que enviar" message. The only existing
code path that calls `generate_alta` for a regular invoice is the shell / management
command path — there is no UI path.

The fix: call `compliance.generate_alta()` immediately after `issue_invoice()` in
`_issue_from_forms()`, using the issuer context already resolved in the view from the
session (`_issuer_from_session`). If the issuer is absent from the session, surface a
warning and issue the invoice without the record (deferred generation is acceptable;
the user can re-enter issuer data and trigger a separate "generate record" action if
needed — but the happy path should auto-generate).

## Requirements

1. **Auto-generate on issue**: Submitting the invoice creation form calls
   `compliance.generate_alta()` and creates a `VerifactuRecord` for the new invoice as
   part of the same request. The detail page shows the submit button active immediately.

2. **Issuer from session**: The `issuer_nif` and `issuer_name` come from
   `_issuer_from_session(request)` (the same source used by PDF generation). If the
   session has no issuer, issue the invoice without a record and show a warning message:
   "Factura emitida sin registro Verifactu — introduce los datos del emisor y vuelve a
   intentarlo."

3. **No double-record**: If `latest_alta_record(invoice)` already returns a record (e.g.
   re-issued after a code bug), do not call `generate_alta` a second time.

4. **Transactional safety**: `generate_alta` runs inside the same `atomic` block as
   `issue_invoice` so a failure rolls back the invoice number assignment. The number is
   never consumed without a corresponding record.

5. **Tests**: At least one integration test confirms that after `invoice_create` POST, the
   invoice has a `VerifactuRecord` with `record_type=ALTA`. The existing tests for the
   "no issuer" path must pass.

## Acceptance Criteria

- [ ] After a successful invoice creation POST (with issuer in session), `invoice.verifactu_records.filter(record_type="alta").count() == 1`
- [ ] The invoice detail page shows `submission_can_submit=True` (submit button visible)
- [ ] If no issuer in session, invoice is issued (200 → redirect), a warning flash appears, and `verifactu_records` is empty
- [ ] All existing 228 tests continue to pass

## Success Measures

n/a — observable via the invoice detail page submit button state; no new metric instrumentation required.

## Rollout

No feature flag needed — this closes a missing step in the existing actor path.

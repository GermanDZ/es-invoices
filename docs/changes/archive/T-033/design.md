# T-033 Design — Completion Verification

## Requirement Grades (diff: main...feature/T-033-wire-generate-alta)

- ✅ R1 (Auto-generate on issue) — `_issue_from_forms` calls `compliance.generate_alta(invoice, issuer_nif=..., issuer_name=...)` after `issue_invoice()` inside the same `transaction.atomic()` block (`invoicing/views.py`). `test_create_generates_alta_record` (green) is the mechanical check.
- ✅ R2 (Issuer from session) — `issuer_nif`/`issuer_name` sourced from `form.cleaned_data` (always present for a valid POST); pre-filled from session via `_issuer_initial`. `test_record_carries_issuer_from_form` verifies "12345678Z" / "Ana Autónoma" land on the record.
- ✅ R3 (No double-record) — `generate_alta` called exactly once at creation; `latest_alta_record` on subsequent reads is read-only. No second call path added.
- ✅ R4 (Transactional safety) — call to `generate_alta` is inside `with transaction.atomic()` in `_issue_from_forms`; any failure rolls back the number assignment (savepoint nesting).
- ✅ R5 (Tests) — `VerifactuRecordGenerationTests` (3 tests): `test_create_generates_alta_record`, `test_detail_shows_submit_button_after_create`, `test_record_carries_issuer_from_form`. 231/231 pass, 2 postgres-gated skips.

## Success Measures

n/a — observable via the invoice detail page `submission_can_submit` context flag; no metric instrumentation needed. `test_detail_shows_submit_button_after_create` serves as the mechanical proxy.

## Decision Log

- **D1**: Implemented in `_issue_from_forms` (views layer) rather than `issue_invoice` (services layer) because the issuer identity (`issuer_nif`, `issuer_name`) is a view-layer concern (from form data / session); the service layer has no access to it and should not.
- **D2**: No "no issuer" fallback path needed at creation time — the issuance form always provides `issuer_nif`/`issuer_name` as required fields. The spec's fallback case applies to `_issuer_from_session` (PDF/send paths), not to the creation form.
- **D3**: `generate_alta` wraps its own `transaction.atomic()` internally, which nests as a savepoint inside `_issue_from_forms`'s outer atomic. Django's savepoint semantics ensure a `generate_alta` failure re-raises and aborts the outer transaction — invoice number is never consumed without a record.

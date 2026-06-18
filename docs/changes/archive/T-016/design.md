# T-016 — In-flight design decisions

Decisions made while implementing; the spec (`plan.md`) stays authoritative for
behavior.

## DD1 — QR embedded as a PNG `data:` URI, not inline SVG

The Operations step said "inline-SVG QR". Implemented instead as a self-contained
PNG `data:` URI (`segno … save(kind="png")` → base64). Rationale: `segno` writes
PNG natively (no Pillow/native dep), WeasyPrint embeds a `data:` URI with no
external asset or filesystem write, and the **observable behavior is identical** —
a scannable QR encoding the AEAT `ValidarQR` URL. This is a rendering-internal
choice, not a behavior change, so no spec re-gate (the requirement — "an embedded
QR encoding the verification URL" — is unchanged). *(Note: `Pillow` arrived
transitively via WeasyPrint, not used by the QR path.)*

## DD2 — Verifactu `Importe` in the QR = `taxable_base + iva_total`

Not `grand_total`. The Verifactu `ImporteTotal` (which the QR must match so a scan
reconciles with the record AEAT received) does **not** subtract IRPF — confirmed
against `compliance/records.py build_registro_alta`
(`importe_total = taxable_base + iva_total`). `build_qr_url` mirrors that exactly;
`test_qr_url_matches_persisted_verifactu_values` locks it.

## DD3 — AEAT formats replicated (not imported) from `compliance`

`_num_serie` (`prefix+number`) and `_fecha_exp` (`DD-MM-YYYY`) are re-stated in
`documents/services.py` with a citation comment rather than importing
`compliance.services._*` (private, and crossing the module interface would violate
the arch-notebook §4 boundary — feature modules depend on compliance only through
its public interface). The **values** are read from the persisted invoice
(satisfying the safeguard "sourced from persisted values"); only the AEAT-fixed
format rule is duplicated. Low drift risk (AEAT spec-fixed); a test asserts the QR
matches the persisted values.

## DD4 — `pypdf` added as a test-only dependency

No `requirements-dev.txt` exists, so `pypdf` (used to extract the PDF text layer
and assert rendered content) is added to `requirements.txt` with a `test-only`
comment to keep CI reproducible.

## DD5 — Recipient email currently requires `to_email`

Neither the recipient snapshot (T-012) nor `clients.Client` (T-015) carries an
email field, so `_recipient_email` yields `''` today and callers must pass
`to_email`. Adding a `Client.email` field is out of this lane's `touches`
(`clients/` is T-015 surface) and would trip the write-fence — deferred. The
`getattr` is forward-compatible: a future `Client.email` resolves automatically.

## DD6 — No "sent" status persisted

`send_invoice_email` performs the send action but writes no status — invoice
status tracking (issued/sent) is **T-018**, which depends on this task. Keeps the
lane read-only on persistence and avoids colliding with T-018's surface.

## Completion verification (step 1a — requirements vs. diff)

Graded against the working tree + `git diff main...HEAD`; all backed by a green test:

- ✅ **Req 1** (compliant PDF render) — `documents/services.py:render_invoice_pdf`
  + `templates/documents/invoice.html`; `test_pdf_carries_mandatory_legal_fields`.
- ✅ **Req 2** (Verifactu QR + legend) — `build_qr_url` + legend block in the
  template; `test_pdf_carries_verifactu_legend`,
  `test_qr_url_matches_persisted_verifactu_values`, `test_qr_base_url_is_config_driven`.
- ✅ **Req 3** (send by email w/ PDF) — `send_invoice_email`;
  `test_sends_one_message_with_pdf_attachment`, `test_from_email_defaults...`.
- ✅ **Req 4** (issued-only guard) — `_require_issued`;
  `test_draft_invoice_is_rejected` (pdf) + `..._and_sends_nothing` (email).
- ✅ **Req 5** (read-only / non-mutating) — no writes in the module;
  `test_render_does_not_mutate_invoice_or_series`.

Full suite: 104 tests green (2 Postgres-gated skips) — 92 prior + 12 new.

## Completion verification (step 1b — success-measure instrumentation)

- ✅ **Instrumentation** — `logger.info("invoice_email_sent num_serie=%s", …)` on
  successful send in `documents/services.py` (NumSerie only, no recipient PII —
  RGPD); asserted by `test_successful_send_emits_instrumentation_log`. The
  denominator (issued-invoice count) already exists in the invoicing data.
- **Read-back date:** 30 days after the first release that exposes send to users
  (gated on T-018 / a send UI — this task ships the capability dark), per
  plan.md §Success Measures.

## Environment note (not a code decision)

The project venv (`.venv`, has Django) and the asdf `python3` shim are distinct
envs; `weasyprint`/`segno`/`pypdf` were installed into `.venv` so `manage.py test`
(which uses `.venv`) sees them. CI installs from `requirements.txt`.

# T-022 — In-flight design decisions

Decisions made during implementation that refine (within scope) the `plan.md`
assumptions. None change the spec's acceptance criteria.

## DD1 — Issuer identity is carried in the session, not persisted on the invoice

`plan.md` assumed the inline issuer fields would be "prefilled from the user's
most recently issued invoice". On inspection, `invoicing.models.Invoice` stores
**no issuer fields** (only the recipient snapshot), and adding them is a model
change the spec forbids ("no new model", "Do not touch invoicing/models.py").
Since `render_invoice_pdf` / `send_invoice_email` need the `Issuer` on
*post-issuance* requests (separate from the create POST), the issuer dict is
stored in `request.session["issuer"]` at issue time and read back by the PDF and
send views. The create form prefills its issuer fields from that same session
key — same UX intent (enter once, reuse), no persistence. If the session lacks
an issuer (e.g. a cold detail-page hit), PDF/send redirect to the detail page
with a message to re-enter.

## DD2 — Recipient comes from a selected saved client (reuses the T-015 bridge)

`plan.md` allowed "select an existing client … inline-only recipient also
allowed". To stay tight and reuse validated logic, the issuance form **requires**
selecting an owner-scoped `clients.Client`; the recipient snapshot is produced by
`clients.services.recipient_snapshot` (which re-asserts the B2B NIF rule). No
free-form recipient entry. This still realizes both guard scenarios:
- Requirement 3 (alt-2a): a draft with zero line items → `issue_invoice` raises.
- Requirement 4 (alt-6a): a B2C client with a blank `tax_id` yields a snapshot
  with empty `recipient_taxid` → `issue_invoice` raises "Missing mandatory
  field(s)", number not consumed.

## DD3 — Draft + issue run in one atomic block

The create POST builds the draft `Invoice` + `LineItem`s and calls
`issue_invoice` inside a single `transaction.atomic()`. A `ValidationError` from
the engine rolls the whole thing back (no orphan draft rows) and re-renders the
form with the message — while `issue_invoice`'s own guarantee keeps
`series.last_number` unchanged.

## Completion verification (step 1a/1b) — 2026-06-20

Graded each requirement against the diff + the green `invoicing.tests.test_views`
suite (9 tests):
- ✅ R1 build draft + line items — `invoice_create` / `IssuanceForm` /
  `LineItemFormSet`; `test_create_issues_invoice_and_assigns_gap_free_number`.
- ✅ R2 gap-free number via `issue_invoice` (view never numbers) —
  `_issue_from_forms`; same test asserts numbers `[1, 2]`.
- ✅ R3 no-line-items blocked, number not consumed —
  `test_no_line_items_is_blocked_without_consuming_a_number`.
- ✅ R4 missing recipient field blocked (B2C blank tax-id → engine raises) —
  `test_missing_recipient_taxid_is_blocked_without_consuming_a_number`.
- ✅ R5 PDF route → `application/pdf` — `invoice_pdf`; `test_pdf_route_returns_application_pdf`.
- ✅ R6 send-by-email to supplied address, marks sent —
  `test_send_emails_pdf_and_marks_sent` (outbox + `sent_at`).
- ✅ R7 IRPF optional — happy path asserts `irpf_retention == 0`;
  `test_irpf_rate_is_applied` covers a non-zero rate.
- ✅ R8 login-required + owner-scoped 404 — `@login_required` + `series__owner`
  filter; `test_create_requires_login`, `test_cross_owner_access_is_404`.

**Success-measure instrumentation (step 1b):** ✅ the `documents` logger
`invoice_email_sent` pre-exists (T-016) and fires on the UI-driven send path;
the green `invoicing` view suite is added in this diff. Read-back: at this
completion (full suite 149 green, 2 PG skips; manual-equivalent template render
asserted in `test_create_and_detail_templates_render`).

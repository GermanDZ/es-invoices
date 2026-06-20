---
id: T-022
title: Invoice issuance UI (create → issue → PDF → email)
status: done
priority: high
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-012, T-016, T-021]
blocks: [T-023, T-024]
touches:
  - invoicing
  - config/urls.py
  - accounts/templates/accounts/landing.html
last-synced: ""
---

# T-022 — Invoice issuance UI (create → issue → PDF → email)

## Story

> **As an** autónomo using FacturaSimple in a browser
> **I want** to build an invoice, issue it, and get/send its PDF from the web UI
> **So that** I can send a legally valid Spanish invoice without touching the API or shell

INVEST check:
✅ Independent (UI over a finished engine) · ✅ Negotiable (issuer/series sourcing
chosen, vetoable) · ✅ Valuable (turns the dark issuance engine into a usable
product) · ✅ Estimable (one app's worth of views/forms/templates) · ✅ Small
(no engine change, no new model) · ✅ Testable (UC-001 flows are observable)

## Analysis Context

- **Domain.** The UI layer for UC-001 (issue a compliant invoice). Wires the
  browser to the already-tested `invoicing.services.issue_invoice` engine
  (T-012) and `documents.services.render_invoice_pdf` / `send_invoice_email`
  (T-016). The `invoicing` app currently has models/services/calc but **no
  views, forms, urls, or templates** — this task adds that surface.
- **Scope boundaries.** Does NOT cover: AEAT submission UI (T-023), corrective /
  annulment UI (T-024), the UC-004/UC-005 behaviour gaps (T-025), a persisted
  issuer-profile model, a `Client.email` field (T-025), or an invoice
  list/status dashboard beyond a minimal post-issue detail page. No change to the
  invoicing engine, compliance module, or submission adapter.
- **Definition of done.** A logged-in user can, in a browser: build a draft
  invoice with ≥1 line item and a recipient, issue it (engine assigns the next
  gap-free series number and computes IVA/IRPF), then view/download the rendered
  PDF and trigger send-by-email. The two UC-001 guard flows (no line items;
  missing mandatory field) are blocked with a visible message and the series
  number is not consumed.

> **Assumption:** Issuer fiscal identity (NIF, name, address) is entered **inline
> on the issuance form** and built into a `documents.services.Issuer` per
> issuance — no new model — prefilled from the user's most recently issued
> invoice when one exists. *(Product-owner decision 2026-06-20; vetoable at review.)*
> **Assumption:** The invoice is attached to the owner's **default (blank-prefix)
> series**, get-or-created if absent; a series-management UI is out of scope.
> *(Vetoable at review.)*
> **Assumption:** The recipient is set by selecting an existing `clients.Client`
> (owner-scoped) which prefills the persisted recipient snapshot
> (`recipient_name` / `recipient_taxid` / `recipient_address`) and sets the
> provenance `client` FK; the snapshot fields remain editable. *(Vetoable.)*
> **Assumption:** The send-by-email recipient address is entered on the send
> action (the `Client` model carries no email until T-025; `send_invoice_email`
> takes `to_email`). *(Vetoable.)*

## Requirements

1. An authenticated owner can build a draft invoice with a recipient and one or
   more line items (description, quantity, unit price, IVA rate) through a
   browser form.
   - **Given** a logged-in user with at least one client **When** they open the
     new-invoice form, select the client, add a line item, and submit
     **Then** an unissued `Invoice` with its `LineItem`(s) is persisted and the
     issuance review/confirm page is shown.
2. Confirming issuance assigns the next gap-free series number and computed
   totals via `invoicing.services.issue_invoice` — the view never assigns a
   number itself.
   - **Given** a draft invoice with valid line items and recipient **When** the
     owner confirms issuance **Then** the invoice is `issued=True` with
     `number == series.last_number` and `taxable_base` / `iva_total` /
     `irpf_retention` / `grand_total` populated by the engine.
3. Issuance is blocked when no line item exists (UC-001 alt-flow 2a).
   - **Given** a draft with zero line items **When** the owner attempts to issue
     **Then** the form re-renders with a "needs at least one line item" message
     and no invoice number is consumed (`series.last_number` unchanged).
4. Issuance is blocked when a mandatory recipient field is missing (UC-001
   alt-flow 6a), surfacing the `ValidationError` without consuming a number.
   - **Given** a draft missing `recipient_name` or `recipient_taxid` **When** the
     owner attempts to issue **Then** the `ValidationError` from
     `issue_invoice` is shown on the form and `series.last_number` is unchanged.
5. After issuance the rendered PDF is retrievable from the UI.
   - **Given** an issued invoice owned by the user **When** they request its PDF
     route **Then** the response is `application/pdf` bytes from
     `documents.services.render_invoice_pdf` (Issuer built from the form's issuer
     fields).
6. After issuance the owner can send the invoice PDF by email to an address they
   supply.
   - **Given** an issued invoice and a recipient email entered on the send action
     **When** the owner submits send **Then** `send_invoice_email(invoice,
     issuer=…, to_email=…)` is called and, on a non-zero send, the invoice shows
     as sent (`sent_at` set).
7. IRPF retention is optional: a zero/unset IRPF rate issues an invoice with no
   retention (UC-001 alt-flow 3a).
   - **Given** the issuance form with IRPF rate left at 0 **When** the invoice is
     issued **Then** `irpf_retention == 0` and `grand_total` excludes retention.
8. Every invoicing view is `@login_required` and owner-scoped — a user can only
   read/act on invoices, series, and clients they own.
   - **Given** invoice X owned by user A **When** user B requests X's
     detail/PDF/send route **Then** the response is 404 (not found for B), never
     X's data.

## Behavior Delta

The UC-001 issuance **engine** already exists and is tested; what this task adds
is the **actor-reachable browser path** to it — previously UC-001 could only be
exercised from tests/shell.

**Added** — behavior that did not exist before (no prior UI surface):
- Browser flow to create, review, and issue an invoice (the `invoicing` app had
  no views/urls/templates).
- In-browser PDF retrieval and send-by-email for an issued invoice.
- Issuer fiscal identity captured inline at issuance time.

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- UC-001 basic flow becomes actor-reachable end to end —
  `docs/use-cases/UC-001-issue-compliant-invoice.md §basic-flow` (steps 1–6 now
  have a UI; no change to the steps themselves, only their reachability).
- Authenticated landing gains an entry point to issuance —
  `accounts/templates/accounts/landing.html` (navigation link only).

**Removed** — none.

## Entities

- **Invoice** (read/write *via service only*) — `invoicing.models.Invoice`
- **LineItem** (new instances via form) — `invoicing.models.LineItem`
- **Series** (read / get-or-create default) — `invoicing.models.Series`
- **Client** (read-only, recipient source) — `clients.models.Client`
- **Issuer** (value object, built per issuance) — `documents.services.Issuer`
- **Invoicing UI** (new) — `invoicing/views.py`, `invoicing/forms.py`,
  `invoicing/urls.py`, `invoicing/templates/invoicing/`

## Approach

Add the missing UI surface **inside the existing `invoicing` app**, mirroring the
function-based, `@login_required`, owner-scoped view shape already used by
`clients` and `accounts`. A create/edit view builds an **unissued** `Invoice`
plus a `LineItem` formset and the issuer/recipient/IRPF fields; a confirm action
calls `issue_invoice` and renders its `ValidationError` back onto the form
(guard flows 2a/6a) so the engine stays the single source of numbering and
validation. Post-issue, a detail page offers a PDF route
(`render_invoice_pdf` → `HttpResponse`) and a send action
(`send_invoice_email`). Views orchestrate only — no calculation, numbering, or
validation logic leaks out of the services.

## Structure

**Add:**
- `invoicing/forms.py` — issuance form (issuer NIF/name/address, recipient via
  client select + editable snapshot, IRPF rate) + `LineItem` formset (min 1).
- `invoicing/views.py` — `invoice_create`, `invoice_issue`, `invoice_detail`,
  `invoice_pdf`, `invoice_send` (all `@login_required`, owner-scoped).
- `invoicing/urls.py` — `app_name = "invoicing"` route table.
- `invoicing/templates/invoicing/invoice_form.html`,
  `invoicing/templates/invoicing/invoice_detail.html`.
- `invoicing/tests/test_views.py` — UC-001 flow coverage.

**Modify:**
- `config/urls.py` — mount `invoicing.urls` at `invoices/`.
- `accounts/templates/accounts/landing.html` — add a "Nueva factura" / "Facturas"
  link.

**Do not touch:**
- `invoicing/services.py`, `invoicing/calc.py`, `invoicing/models.py` — the
  numbering/validation/calculation engine; UI consumes it unchanged (a pure
  refactor here would need `/openup-sync-spec`, not this task).
- `documents/services.py` — consumed as-is (`render_invoice_pdf` /
  `send_invoice_email`).
- `submission/*`, `compliance/*` — AEAT submission is T-023, out of scope.

## Operations

- [x] Add `invoicing/forms.py`: an issuance form with issuer fields (NIF, name,
      address), recipient via owner-scoped client select that prefills the
      editable recipient snapshot, an optional IRPF rate, and a `LineItem`
      formset requiring ≥1 row.
- [x] Add `invoicing/views.py`: `invoice_create` (build draft + render form),
      `invoice_issue` (POST → `issue_invoice`; catch `ValidationError` →
      re-render with the message, number not consumed), `invoice_detail`,
      `invoice_pdf` (build `Issuer`, `render_invoice_pdf` → `application/pdf`
      response), `invoice_send` (POST → `send_invoice_email` with `to_email`).
      All `@login_required` and filtered to `request.user`.
- [x] Prefill the issuer fields from the user's most recently issued invoice and
      get-or-create the owner's default (blank-prefix) series for new drafts.
- [x] Add `invoicing/urls.py` + the two templates; mount `invoicing.urls` at
      `invoices/` in `config/urls.py`; add the issuance link to the accounts
      landing template.
- [x] (tester) Add `invoicing/tests/test_views.py`: happy path (create → issue →
      PDF is `application/pdf` → send marks sent), alt-2a (no line items
      blocked), alt-6a (missing recipient field blocked, `last_number`
      unchanged), IRPF-off path, and login-required + owner-scoping (cross-owner
      access → 404).
- [x] Run `python manage.py test` (full suite) and a manual browser smoke (login
      → create → add items → issue → open PDF → send via the console email
      backend); confirm two consecutive issues receive consecutive gap-free
      numbers.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `AGENTS.md` — repository/app conventions for this Django project.
- `docs/architecture-notebook.md` §4 (Document & delivery / module boundaries).

## Safeguards

- **No-go zones.** No change to invoice numbering, IVA/IRPF calculation, legal
  validation, or PDF/email rendering logic — `issue_invoice`, `calc`, and
  `documents.services` are consumed unchanged. The UI never assigns a number or
  computes totals itself.
- **Owner-scoping invariant.** Every queryset (invoices, series, clients) is
  filtered by `request.user`; no route exposes another owner's data (Requirement
  8). Cross-owner access returns 404.
- **Reversibility.** Additive: a new app surface plus one `config/urls.py` mount
  and one landing-template link. Back out by removing the mount and the link; no
  data migration, no model change.
- **Token / size budget.** Templates ≤ ~120 lines each; views stay thin
  (orchestration only — no business logic).

## Rollout

**Flagged?** No. The change is an additive UI mounted at a **new** URL prefix
(`invoices/`); no existing route or behavior changes until a user navigates to
the new pages, so a feature flag would add no safety. Back out by removing the
`config/urls.py` mount and the landing link.

`n/a — additive new surface, reachable only via new routes; not a flag candidate.`

## Success Measures

We expect the **UC-001 actor path to be exercisable end-to-end through the
browser** — at least one invoice issued and one PDF emailed via the new UI in the
release smoke (vs. zero today, where all issuance is test/shell-only).
Instrumentation: the existing `documents` logger emits `invoice_email_sent
num_serie=…` on a successful UI-driven send, plus the green `invoicing` view test
suite. Read-back: at task completion (manual smoke + `python manage.py test`).

## Verification

- `python manage.py test` passes, including the new `invoicing/tests/test_views.py`.
- Manual browser smoke: login → create invoice with a client + ≥1 line item →
  issue → PDF opens as `application/pdf` → send via the console email backend
  prints the message; two consecutive issues get consecutive numbers.
- Guard flows: issuing with no line items and with a missing recipient field both
  block with a message and leave `series.last_number` unchanged.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅.

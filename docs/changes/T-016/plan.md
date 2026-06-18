---
id: T-016
title: PDF generation + send by email
status: ready   # proposed → ready → in-progress → done → verified
priority: medium
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-012]
blocks: [T-018]
last-synced: ""
touches:
  - documents/
  - config/settings.py
  - config/urls.py
  - requirements.txt
  - docs/changes/T-016/
---

# T-016 — PDF generation + send by email

## Story

> **As a** Spanish autónomo who has just issued a compliant invoice,
> **I want** a clean PDF of it delivered to my client by email,
> **So that** I finish the whole "issue → send" job in one sitting without
> leaving the app or hand-building a document.

INVEST check:
✅ Independent (reads an already-issued invoice; no numbering/compliance change) ·
✅ Negotiable (engine + provider are swappable) · ✅ Valuable (closes S-3 / UC-001
postcondition "invoice available as PDF") · ✅ Estimable (one new app, two services) ·
✅ Small (render + send, no status model) · ✅ Testable (PDF content + email outbox).

## Analysis Context

- **Domain.** The architecture-notebook §4 **"Document & delivery"** module — the
  last step of UC-001 ("…then makes the PDF available"). Renders an **already
  issued** `invoicing.Invoice` to a PDF and delivers it by email. It is a pure
  **consumer** of the invoicing core: read-only on the invoice, no numbering, no
  Verifactu record generation.
- **Scope boundaries.** Does **not** persist a "sent" status (that is **T-018**,
  which depends on this). Does **not** add an issuing-business/account model —
  issuer fiscal data is **passed in** by the caller, mirroring
  `compliance.services.generate_alta(..., issuer_nif=, issuer_name=)`. Does **not**
  build a UI/web view (services + template only); a thin view can come with T-018.
  Does **not** re-validate legal fields — that is the compliance module's job at
  issue time.
- **Definition of done.** `documents.render_invoice_pdf(invoice, issuer=…)` returns
  PDF bytes carrying every mandatory legal field plus the VERI\*FACTU legend + QR;
  `documents.send_invoice_email(invoice, issuer=…, to_email=…)` delivers it as an
  attachment through Django's configured email backend; both refuse a non-issued
  invoice; tests cover content, delivery, and the guard.

Open questions resolved by default (all **vetoable at review**):

> **Assumption:** PDF engine is **WeasyPrint** (HTML+CSS template → PDF), per the
> arch-notebook "WeasyPrint / ReportLab" note — chosen for a templated, easily
> restyled invoice over hand-laid ReportLab primitives. *(Vetoable at review.)*
> **Assumption:** QR is generated with **`segno`** (pure-Python, no Pillow/system
> deps) and embedded as inline SVG — keeps the lean/bootstrapped constraint
> (arch §5). *(Vetoable.)*
> **Assumption:** The Verifactu **QR + "VERI\*FACTU" legend are IN scope** for this
> PDF. A Verifactu invoice is not legally complete without them, and "compliance is
> non-negotiable" (scope §4) overrides the roadmap line's terse "clean PDF" framing.
> *(Vetoable — if the PM scopes QR out, drop Requirement 2 and its dep.)*
> **Assumption:** Email uses **Django's pluggable backend** (`django.core.mail`):
> `console` backend for local/dev, real SMTP via `EMAIL_*` env in deployed
> environments — the concrete provider is config, not code. *(Vetoable.)*
> **Assumption:** Issuer fiscal identity (name, NIF, address) is a caller-supplied
> value object, not read from a new model. *(Vetoable.)*

## Requirements

1. **Compliant PDF render.** `render_invoice_pdf(invoice, *, issuer)` returns PDF
   bytes for an issued invoice containing all mandatory legal fields: issuer
   (name, NIF, address), recipient snapshot (name, taxid, address), series+number,
   issue date, every line item (description, quantity, unit price, IVA rate),
   the taxable base, IVA total, IRPF retention, and grand total.
   - **Given** an issued invoice with two line items and an IRPF rate
     **When** `render_invoice_pdf` is called **Then** the returned bytes are a
     valid PDF whose extracted text contains the series+number, both line
     descriptions, the recipient NIF, and the grand total formatted as currency.

2. **Verifactu QR + legend.** The PDF carries the literal legend **"VERI\*FACTU"**
   (or "Factura verificable en la sede electrónica de la AEAT") and a QR encoding
   the AEAT `ValidarQR` URL built from `VERIFACTU_QR_BASE_URL` + issuer NIF,
   `NumSerie`, `FechaExpedicion`, and `ImporteTotal`.
   - **Given** the QR base URL is configured **When** an issued invoice is rendered
     **Then** the PDF contains the legend text and an embedded QR image, and the
     encoded URL contains the invoice's `numserie`, `fecha`, and `importe`
     query parameters matching the invoice's persisted values.

3. **Send by email with PDF attached.** `send_invoice_email(invoice, *, issuer,
   to_email=None)` renders the PDF and sends one message via the configured
   backend, with the PDF attached and a Spanish subject/body; `to_email` defaults
   to the recipient's email when available.
   - **Given** the locmem email backend **When** `send_invoice_email` is called for
     an issued invoice **Then** exactly one message is in the outbox, addressed to
     the recipient, with one `application/pdf` attachment whose bytes are a PDF.

4. **Issued-only guard.** Both services reject a draft (not-yet-issued) invoice.
   - **Given** a draft invoice (`issued=False`) **When** either service is called
     **Then** it raises `ValueError`/`ValidationError` and no email is sent.

5. **Read-only / non-mutating.** Rendering and sending never write to the invoice,
   its line items, the numbering series, or any compliance record.
   - **Given** an issued invoice **When** it is rendered and emailed **Then** the
     invoice row, its `LineItem`s, and the `Series.last_number` are byte-for-byte
     unchanged (verified by comparing field values before/after).

## Behavior Delta

`n/a — all Added.` This task realizes an existing UC-001 postcondition that had no
implementation and adds email delivery; it changes no currently-implemented Ring-1
behavior.

**Added** — behavior that did not exist before:
- Render an issued invoice to a compliant PDF — realizes the postcondition
  "The invoice is available as a PDF" (`docs/use-cases/UC-001-issue-compliant-invoice.md §postconditions`,
  step "makes the PDF available" in §main-flow), previously unimplemented.
- Deliver the invoice PDF to the recipient by email — `docs/scope.md §S-3`,
  Vision §4.3 (no prior Ring-1 flow).
- Embed the Verifactu verification QR + VERI\*FACTU legend on the PDF
  (`docs/scope.md §4` compliance guardrail).

## Entities

- **render_invoice_pdf / send_invoice_email** (new) — `documents/services.py`
- **Issuer** value object (new) — caller-supplied fiscal identity (name, nif,
  address) — `documents/services.py` (dataclass), not a DB model.
- **Invoice / LineItem / Series** (read-only) — `invoicing/models.py`
- **VerifactuRecord** (read-only, optional) — `compliance/models.py` — source of
  the persisted `num_serie` / `importe_total` the QR URL must match.
- **Invoice HTML template** (new) — `documents/templates/documents/invoice.html`

## Approach

Add a new `documents` Django app realizing the arch-notebook "Document & delivery"
module. A single Django HTML template renders the invoice; WeasyPrint converts it
to PDF bytes; `segno` produces an inline-SVG QR from the AEAT `ValidarQR` URL built
off persisted invoice values. A thin `send_invoice_email` service wraps
`django.core.mail.EmailMessage`, attaching the rendered bytes. Issuer fiscal data
is passed in (a small dataclass), keeping this module a read-only consumer of the
invoicing core with no new persistence — the same boundary `compliance.generate_alta`
already uses. Email backend and QR base URL come from settings/env, so dev runs use
the console/locmem backend and deployments wire a real provider via config alone.

## Structure

**Add:**
- `documents/__init__.py`, `documents/apps.py`
- `documents/services.py` — `Issuer` dataclass, `render_invoice_pdf`,
  `send_invoice_email`, `build_qr_url`
- `documents/templates/documents/invoice.html` — invoice layout + legend + QR slot
- `documents/tests/__init__.py`, `documents/tests/test_pdf.py`,
  `documents/tests/test_email.py`

**Modify:**
- `requirements.txt` — add `weasyprint`, `segno`
- `config/settings.py` — add `documents` to `INSTALLED_APPS`; add `EMAIL_BACKEND`
  (console default for dev) + `DEFAULT_FROM_EMAIL` + `VERIFACTU_QR_BASE_URL` via `_env`
- `config/urls.py` — only if a render/download view is added (deferred; likely untouched)

**Do not touch:**
- `invoicing/models.py`, `invoicing/services.py` — read-only consumer; no numbering
  or immutability change belongs here.
- `compliance/`, `submission/` — record generation and AEAT submission are unrelated
  to document delivery; read `VerifactuRecord` only, never write.
- Any "sent" status field — that is **T-018** (depends on this); adding it here
  would collide.

## Operations

- [ ] Add `weasyprint` + `segno` to `requirements.txt`; add `documents` to
      `INSTALLED_APPS` and `EMAIL_BACKEND`/`DEFAULT_FROM_EMAIL`/`VERIFACTU_QR_BASE_URL`
      settings (env-driven, console backend default) in `config/settings.py`.
- [ ] Scaffold the `documents` app (`apps.py`, `__init__.py`) and the
      `Issuer` dataclass + `build_qr_url(invoice, issuer)` helper in
      `documents/services.py`.
- [ ] Author `documents/templates/documents/invoice.html` rendering all mandatory
      legal fields, the VERI\*FACTU legend, and the inline-SVG QR.
- [ ] Implement `render_invoice_pdf(invoice, *, issuer)` (issued-only guard →
      template render → WeasyPrint → bytes) in `documents/services.py`.
- [ ] Implement `send_invoice_email(invoice, *, issuer, to_email=None)` building an
      `EmailMessage` with the PDF attached, defaulting `to_email` to the recipient.
- [ ] (tester) Write `test_pdf.py` (Req 1, 2, 4, 5) and `test_email.py`
      (Req 3, 4) using the locmem backend; run `python manage.py test documents`.
- [ ] (tester) Run the full suite (`python manage.py test`) to confirm no
      regression in invoicing/compliance/submission.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `AGENTS.md` — repo-level agent conventions
- `docs/architecture-notebook.md §4` — module boundaries (Document & delivery is a
  consumer of the invoicing core through its models only).

## Safeguards

- **Read-only invariant.** No write to `Invoice`, `LineItem`, `Series`, or
  `compliance` rows from this module (Requirement 5).
- **No new persistence.** No model/migration in `documents`; issuer data is passed
  in. Reversibility: deleting the app + the three settings lines + two requirements
  fully backs the change out.
- **No-go zones.** Gap-free numbering, invoice immutability, Verifactu record
  generation, and AEAT submission behavior must not change.
- **Compliance content.** QR URL fields must be sourced from the invoice's
  **persisted** values (the same the Verifactu record was built from), never
  recomputed independently — see `compliance/records.py` field order.
- **Token / size budget.** `invoice.html` ≤ ~150 lines; `services.py` ≤ ~120 lines.

## Rollout

**Flagged? No.** This adds a new, inert module — nothing renders or sends until a
caller (or a later UI task) invokes the services, so the code path is dark until
explicitly wired. A flag would add no safety over that natural gating. Delivery
reaches users only when T-018 (or a UI task) calls these services; environment
config (`EMAIL_BACKEND`, `VERIFACTU_QR_BASE_URL`) is the real switch: console/locmem
backend in local/dev → real SMTP + production QR base URL in production. Kill-switch
equivalent: point `EMAIL_BACKEND` at the console backend to stop outbound mail
without a redeploy. No flag-removal follow-up needed (no flag introduced).

## Success Measures

We expect **the share of issued invoices that are also delivered to the client from
within the app (vs. exported/sent manually)** to reach **≥ 60 %** within **the first
30 days** of the send feature being wired to a UI. Instrumentation: count of
`send_invoice_email` successes over count of issued invoices in the window (log/event
on send). Read-back: **30 days after the first release that exposes send to users**
(i.e. with T-018 or the send UI — this task ships the capability dark, so the
read-back is gated on that exposure, not on this merge).

## Verification

- `python manage.py test documents` is green (Req 1–5).
- `python manage.py test` shows no regression elsewhere.
- Manual spot-check: render one issued invoice, open the PDF, confirm the VERI\*FACTU
  legend + scannable QR and all legal fields are present.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅ or an explicit gap call-out.

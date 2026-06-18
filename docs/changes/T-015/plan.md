---
id: T-015
title: "Client/contact management (recipient fiscal data)"
status: ready   # proposed → ready → in-progress → done → verified
priority: medium   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/roadmap.md#construction   # link to originating plan, if any
depends-on: [T-012]
blocks: [T-018]
touches: [clients, invoicing, config]
last-synced: ""    # full git SHA of last code↔spec sync (set by /openup-sync-spec)
---

# T-015 — Client/contact management (recipient fiscal data)

## Story

> **As an** autónomo issuing invoices
> **I want** to create and reuse client records (fiscal name, NIF/CIF, address)
> **So that** I can select a saved recipient when issuing instead of re-typing fiscal data each time.

INVEST check:
✅ Independent — depends only on T-012 (invoicing core), already done · ✅ Negotiable — model + CRUD shape open · ✅ Valuable — realises S-1 / UC-003, cuts time-to-first-invoice (Q-4) · ✅ Estimable — 1–2 sessions · ✅ Small — one new app + a provenance FK · ✅ Testable — validation + scoping + snapshot have clear assertions

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Client management module (architecture-notebook §4) — recipient
  fiscal data for B2B (NIF/CIF) and B2C (final consumers, simplified-invoice
  rules, scope.md D-2). Realises S-1 / REQ-003 / UC-003.
- **Scope boundaries.** This task delivers the `Client` entity, its
  owner-scoped CRUD, Spanish tax-id validation, and a service that turns a saved
  client into the recipient snapshot the invoice already carries. It does **not**
  build an invoice-issuance UI (none exists yet — T-012 shipped model + services
  only); wiring client-selection into an issuance *form* lands when that UI is
  built. It does **not** alter the legal recipient snapshot model on `Invoice`
  (denormalised on purpose, T-012) — the snapshot stays the source of truth.
- **Definition of done.** A logged-in user can create/edit/delete their own
  clients through web views; a B2B client requires a checksum-valid NIF/CIF; a
  B2C client may omit it; `clients.services` can produce a recipient snapshot
  from a client; an optional `Invoice.client` FK records provenance without
  displacing the snapshot. Tests green; `python3 manage.py check` clean.

> **Assumption:** Clients are typed **B2B** (NIF/CIF mandatory) or **B2C**
> (final consumer; NIF/CIF optional per scope.md D-2 simplified-invoice rules).
> When a tax-id is present on either type it is format+checksum validated.
> *(Vetoable at review — resolves the UC-003 self-critique "validation depth" point.)*
> **Assumption:** Tax-id validation is **format + control-character checksum**
> for Spanish DNI/NIE/CIF (deterministic, cheap), not a live AEAT lookup.
> *(Vetoable at review.)*
> **Assumption:** Client management is a **new Django app `clients`**, mirroring
> the per-subsystem app layout (`certificates`, `compliance`, `invoicing`,
> `submission`) and architecture-notebook §4's distinct module. *(Vetoable.)*

## Requirements

1. A `Client` stores recipient fiscal data — fiscal name, client type (B2B/B2C),
   tax-id, address — owned by exactly one user.
   - **Given** an authenticated user **When** they submit a client with fiscal
     name "ACME SL", type B2B and a valid CIF **Then** a `Client` is persisted
     linked to that user and appears in their client list.
2. A B2B client requires a tax-id that passes Spanish format **and** checksum
   validation; an invalid or missing tax-id on a B2B client is rejected with a
   field error and nothing is saved.
   - **Given** the create-client form with type B2B **When** the user submits
     CIF "B00000000" (bad control char) or leaves the tax-id blank **Then** the
     form is rejected with a tax-id error and no `Client` row is created.
3. A B2C client may omit the tax-id (simplified-invoice rule); when a tax-id is
   supplied on a B2C client it is still format+checksum validated.
   - **Given** type B2C **When** the user submits with an empty tax-id **Then**
     the client is saved; **and When** a non-empty malformed tax-id is supplied
     **Then** it is rejected with a tax-id error.
4. Client access is owner-scoped: a user can list, view, edit and delete only
   their own clients and never another user's.
   - **Given** client X owned by user A **When** user B requests X's edit/delete
     view **Then** the response is 404 (not found in B's queryset) and X is
     unchanged.
5. `clients.services` produces a recipient snapshot (name, tax-id, address) from
   a saved client, suitable for the `Invoice` recipient fields; a B2B client with
   an invalid/missing NIF cannot yield a usable snapshot for issuance.
   - **Given** a valid B2B client **When** `recipient_snapshot(client)` is called
     **Then** it returns a dict of `recipient_name` / `recipient_taxid` /
     `recipient_address` matching the client; **and Given** a B2B client whose
     NIF fails validation **When** a snapshot is requested for issuance **Then**
     it raises `ValidationError` and no snapshot is produced.
6. Client CRUD is reachable only by authenticated users through web views
   (list / create / edit / delete), following the certificates-app view pattern.
   - **Given** an anonymous request **When** it hits any clients view **Then** it
     is redirected to login; **Given** an authenticated user **Then** the list,
     create, edit and delete views respond and mutate only via POST.

## Behavior Delta

Greenfield for client management — `n/a — all Added`, except one additive link on
the existing invoice.

**Added** — behavior that did not exist before:
- Client CRUD with owner scoping — realises `docs/use-cases/UC-003-manage-client.md §basic-flow`.
- Spanish tax-id format+checksum validation (DNI/NIE/CIF) — realises
  `docs/use-cases/UC-003-manage-client.md §alt-flow-3a` (invalid NIF/CIF rejected).
- Recipient snapshot built from a saved client (`clients.services.recipient_snapshot`).

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- `Invoice` gains an optional `client` FK recording recipient provenance; the
  denormalised recipient snapshot remains the legal source of truth, so issuance
  behavior in `docs/use-cases/UC-001-issue-compliant-invoice.md §basic-flow` is
  unchanged (the FK is additive, nullable, never read by numbering/compliance).

**Removed** — none.

## Entities

- **Client** (new) — `clients/models.py` — fiscal name, `client_type` (B2B/B2C),
  `tax_id`, address, `owner` FK.
- **Spanish tax-id validator** (new) — `clients/validation.py`.
- **Recipient snapshot service** (new) — `clients/services.py`.
- **Invoice** (modified, additive only) — `invoicing/models.py` — nullable
  `client` FK (provenance).
- **Recipient snapshot fields** (read-only) — `Invoice.recipient_name/_taxid/_address`
  — the snapshot target, not altered by this task.

## Approach

Add a self-contained `clients` Django app mirroring the existing per-subsystem
apps (architecture-notebook §4, AD-1 modular monolith). The `Client` model is
owner-scoped; tax-id validity is enforced at the model/form layer via a small
pure validator in `clients/validation.py` (format + Spanish control-char
checksum), with B2C allowed to omit the id. CRUD follows the certificates app's
`@login_required` view shape, querying `Client.objects.filter(owner=request.user)`
so scoping is structural. A thin `clients.services.recipient_snapshot` bridges a
saved client into the invoice's existing denormalised recipient fields — the
snapshot stays the legal record; the new nullable `Invoice.client` FK only
records provenance and is never consulted by numbering or compliance.

## Structure

**Add:**
- `clients/__init__.py`, `clients/apps.py`
- `clients/models.py` — `Client`
- `clients/validation.py` — `validate_spanish_taxid` (DNI/NIE/CIF checksum)
- `clients/forms.py` — `ClientForm` (type-conditional tax-id rule)
- `clients/services.py` — `recipient_snapshot(client)`
- `clients/views.py` — list / create / edit / delete (`@login_required`, owner-scoped)
- `clients/urls.py` — `app_name = "clients"`
- `clients/migrations/0001_initial.py`
- `clients/templates/clients/list.html`, `form.html`, `confirm_delete.html`
- `clients/tests/__init__.py`, `test_validation.py`, `test_views.py`, `test_services.py`, `factories.py`
- `invoicing/migrations/0002_invoice_client.py` — nullable `client` FK

**Modify:**
- `config/settings.py` — add `"clients"` to `INSTALLED_APPS`
- `config/urls.py` — `include("clients.urls")`
- `invoicing/models.py` — add nullable `client = ForeignKey("clients.Client", null=True, blank=True, on_delete=PROTECT)` (provenance only)

**Do not touch:**
- `invoicing/services.issue_invoice` numbering/locking logic — out of scope; the
  client FK is additive and not read by issuance.
- `compliance/` internals (AD-2) — recipient *legal-field* validation for issuance
  stays in the versioned module; client-form validation is a separate UX gate.

## Operations

- [ ] Scaffold the `clients` app (`apps.py`, register in `config/settings.py`), add `Client` model (owner FK, `client_type`, `tax_id`, fiscal name, address) and its initial migration; run `python3 manage.py check`.
- [ ] Implement `clients/validation.py` `validate_spanish_taxid` (DNI/NIE/CIF format + control-char checksum) with unit tests for valid + invalid cases.
- [ ] Implement `clients/forms.py` `ClientForm` enforcing the type-conditional tax-id rule (B2B mandatory+valid; B2C optional, validated when present).
- [ ] Implement `clients/services.py` `recipient_snapshot(client)` returning the invoice recipient fields, raising `ValidationError` for an unusable B2B client; add `invoicing/models.py` nullable `client` FK + migration.
- [ ] Implement owner-scoped CRUD views + `urls.py` + templates following the certificates app pattern (`@login_required`, queryset filtered by `owner`); wire into `config/urls.py`.
- [ ] (tester) Add `clients/tests/` covering requirements 1–6 (persistence+scoping, B2B/B2C validation, snapshot success/failure, auth redirect); run the full suite + `python3 manage.py check` and confirm green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/architecture-notebook.md` §3–§4 — AD-1 modular monolith, module decomposition
- Existing app patterns — `certificates/views.py` (CRUD shape), `invoicing/models.py` (owner-scoped model + migration style)

> Reference, don't copy.

## Safeguards

Invariants and limits that must hold:
- **No-go zones.** Gap-free numbering (`invoicing/services.issue_invoice`) and the
  compliance module (AD-2) are unchanged; the recipient *snapshot* on `Invoice`
  stays the legal source of truth — the new `client` FK is provenance only,
  nullable, and never read by numbering or compliance.
- **Owner scoping is structural.** Every client query filters by
  `owner=request.user`; cross-owner access returns 404, never another user's row.
- **Reversibility.** Additive only — new app + one nullable FK. Back out by
  removing the app from `INSTALLED_APPS`/urls and reverting the two migrations;
  no issued-invoice data is touched.
- **Size budget.** One app, ≤ ~6 source files plus templates/tests; no new
  third-party dependency (validator is pure Python).

## Rollout

**Flagged? No.** The feature is purely additive — a new Django app reachable only
through new `@login_required` routes and nav; it changes no existing issued-invoice
behavior and the `Invoice.client` FK is nullable. A flag would add no safety
(nothing to toggle off that isn't already gated behind new auth'd routes), so
shipping unflagged is the lower-risk choice. Reaches users by deploying the new
routes. `n/a — no flag` (additive, auth-gated).

## Success Measures

We expect **the share of invoices issued with a linked saved client
(`Invoice.client` non-null)** to reach **≥ 60%** within **30 days** of a user
creating their first client, evidencing that client reuse replaces repeated
manual recipient entry (the S-1 / Q-4 time-to-first-invoice driver).
Instrumentation: **non-null rate of `Invoice.client` among invoices issued by
users with ≥1 client**, read from the datastore. Read-back: **30 days after the
clients feature reaches beta users.**

## Verification

How a reviewer confirms the task is done:
- `python3 manage.py check` is clean and `python3 manage.py test clients invoicing` is green.
- New-user smoke: create a B2B client with a valid CIF (saves), an invalid CIF
  (rejected), a B2C client with no tax-id (saves); confirm a second user cannot
  open the first user's client edit/delete view (404).
- `clients.services.recipient_snapshot` returns the recipient fields for a valid
  client and raises for an invalid-NIF B2B client.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅.

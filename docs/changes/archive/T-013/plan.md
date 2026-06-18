---
id: T-013
title: "Compliance/Verifactu module: record gen + hash-chain + XAdES"
status: done
priority: high   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-010, T-012]
blocks: [T-014, T-017]
last-synced: ""
---

# T-013 — Compliance/Verifactu module: record gen + hash-chain + XAdES

## Story

> **As a** Spanish autónomo who issues invoices through FacturaSimple
> **I want** each issued invoice turned into a legally-conformant, hash-chained,
> signed Verifactu record
> **So that** my invoices are reportable to the AEAT under Veri\*Factu and the
> chain proves none was altered or deleted after the fact.

INVEST check:
✅ Independent — module sits behind its own interface; submission (T-014) is separate
✅ Negotiable — XAdES profile / library are open at the design layer
✅ Valuable — reportability is the legal reason the product exists (Vision §2)
✅ Estimable — record builder + huella already proven in the T-010 PoC
✅ Small — one module, no network, no UI
✅ Testable — XSD-conformance, huella reproduction, signature verification are all checkable

## Analysis Context

- **Domain.** The compliance/Verifactu module (AD-2, S-4): the single versioned
  home for every Verifactu/AEAT rule — legal-field validation, `RegistroAlta`
  generation, the `huella` hash-chain, XAdES signing, and `RegistroAnulación`
  generation. It consumes an issued `invoicing.Invoice` (T-012) and the user's
  certificate material (`certificates.services`, T-011) and produces persisted,
  signed records ready for submission.
- **Scope boundaries.** This task **generates and persists** records; it does
  **not** submit them to the AEAT — SOAP transport, accepted/rejected capture,
  and retry are T-014 (the AD-3 adapter). No UI, no PDF (T-016), no client CRUD
  (T-015). Común-territory **Veri\*Factu only**; TicketBAI/foral is out of v1
  (AD-3 scope, N-6). No mutation of the issued invoice (T-012 immutability).
- **Definition of done.** A new versioned `compliance` module exposes a public
  API that, given an issued invoice, validates its legal fields, builds an
  XSD-conformant `RegistroAlta` with a spec-correct `huella` chained to the prior
  record for the same issuer, applies a XAdES-enveloped signature using the
  user's certificate, and persists a `VerifactuRecord`. An annulment path
  produces a chained, signed `RegistroAnulación` referencing an existing record.
  All exercised by a green `compliance` test suite.

> **Assumption:** XAdES per-record signing is **included** per AD-2 and the
> roadmap line, even though the chosen Veri\*Factu *remisión* submission mode
> (AD-3) derives record integrity from cert-authenticated mTLS + the `huella`
> chain, where a per-record XAdES signature is not strictly required by the
> sending service. Building the signing capability honours the architecture
> decision; the nuance is recorded here so the founder can de-scope it. *(Vetoable at review.)*

> **Assumption:** The hash-chain is **per issuer** (`IDEmisorFactura` / obligado
> NIF), spanning all series — matching the AEAT `huella` field order and the
> T-010 PoC, not per numbering series. *(Vetoable at review.)*

> **Assumption:** XAdES signing uses `lxml` + an XML-DSig/XAdES library added to
> `requirements.txt`; the architect pins the exact library. Tests sign with a
> self-signed fixture certificate, never the founder's real cert (mirrors T-010
> DD2). *(Vetoable at review.)*

## Requirements

1. **Versioned module interface (AD-2/R-01).** All Verifactu rules live in one
   `compliance` module exposing an explicit `MODULE_VERSION` and a public API;
   callers (e.g. T-014) never import its internals.
   - **Given** the `compliance` package **When** a caller imports its public API
     **Then** `MODULE_VERSION` is exposed and record generation is reachable
     without importing any private submodule (`compliance.records`,
     `compliance.signing`, …).
2. **Legal-field validation blocks malformed records (Q-1).** A record is never
   generated from an invoice missing a mandatory Verifactu field; validation
   fails loudly and persists nothing.
   - **Given** an issued invoice with no `recipient_taxid` **When**
     `generate_alta` is called **Then** it raises a validation error and **no**
     `VerifactuRecord` row is created.
3. **XSD-conformant `RegistroAlta` from a T-012 invoice.** Generation builds a
   `RegistroAlta` whose `Desglose` is derived from the invoice's line items
   grouped by IVA rate (reusing `invoicing.calc` grouping), and the record
   validates against the published Verifactu XSD.
   - **Given** an issued invoice with two line items at 21% and one exempt
     **When** `generate_alta` runs **Then** the produced XML has one
     `DetalleDesglose` per rate group with bases/cuotas matching
     `calc.compute_totals`, and `validate_local` against the XSD returns ok.
4. **Spec-correct `huella`.** The `huella` is SHA-256 over the AEAT canonical
   field concatenation (`IDEmisorFactura&NumSerieFactura&FechaExpedicionFactura&TipoFactura&CuotaTotal&ImporteTotal&Huella&FechaHoraHusoGenRegistro`),
   UTF-8 → upper hex; the first record for an issuer carries `PrimerRegistro=S`.
   - **Given** the first record for an issuer with known field values **When**
     the `huella` is computed **Then** it equals the SHA-256 upper-hex of the
     spec-ordered concatenation with an empty previous-`Huella`, and the XML
     carries `Encadenamiento/PrimerRegistro=S`.
5. **Hash-chain linkage, fork-safe.** Each new record links to the most recent
   prior record for the same issuer (`RegistroAnterior` carrying its
   `IDFactura` + `Huella`); concurrent generation cannot give two records the
   same predecessor (transactional row-lock on the chain tail, mirroring T-012
   numbering, AD-6).
   - **Given** an issuer with one accepted record **When** a second record is
     generated **Then** its `RegistroAnterior/Huella` equals the first record's
     `huella` and `previous_record` FK points at it; **and given** two
     generations race on PostgreSQL **Then** they serialise into a linear chain
     (no two records share a predecessor).
6. **XAdES-enveloped signature.** The generated record carries a XAdES-enveloped
   XML-DSig signature produced with the user's certificate material; the
   signature verifies against that certificate.
   - **Given** a fixture-signed record **When** the signature is verified with
     the signing certificate **Then** verification succeeds, and **when** one
     byte of the signed content is altered **Then** verification fails.
7. **Annulment record (UC-005).** An annulment path generates a chained, signed
   `RegistroAnulación` referencing an existing record's `IDFactura`, persisted as
   a `VerifactuRecord` of type `anulacion`.
   - **Given** an issuer with an existing alta record **When**
     `generate_anulacion` is called for it **Then** a `VerifactuRecord` of type
     `anulacion` is persisted whose record references the original `IDFactura`,
     is chained on the prior `huella`, and is signed.

## Behavior Delta

n/a — all Added. This task introduces a new internal capability (Verifactu record
generation, chaining, signing). Its output is **not yet user-observable** — nothing
is submitted to the AEAT and no UC main flow changes its externally-visible outcome
until the submission adapter (T-014) wires it in. No existing Ring-1 behavior is
Modified or Removed.

**Added** — behavior that did not exist before:
- Generation + persistence of a signed, hash-chained Verifactu `RegistroAlta`
  for an issued invoice. Realises the reportability half of
  `docs/use-cases/UC-002-submit-invoice-to-aeat.md` (record produced; transport is T-014).
- Generation of a Verifactu `RegistroAnulación`. Realises
  `docs/use-cases/UC-005-annul-invoice-record.md §basic-flow` step 4 (the record
  is built + chained here; submission + invoice-state change are T-014/T-017).

## Entities

- **`compliance` module** (new) — `compliance/__init__.py` (public API + `MODULE_VERSION`), the AD-2 versioned home.
- **VerifactuRecord** (new) — `compliance/models.py`; persisted record: FK to `Invoice`, `record_type` (alta|anulacion), `issuer_nif`, `num_serie`, `huella`, `previous_record` self-FK, `fecha_hora_gen`, signed `xml`, `module_version`.
- **Invoice / LineItem / Series** (read-only) — `invoicing/models.py`; the source of legal-field + Desglose data. Not mutated.
- **`invoicing.calc`** (read-only) — `invoicing/calc.py`; IVA rate-group totals reused to build the `Desglose`.
- **CertMaterial** (read-only) — `certificates/services.py` `get_cert_material(user)`; supplies the signing key/cert.
- **PoC builder** (reference) — `poc/aeat-preproduccion/alta_builder.py`; `compute_huella` + `build_regfactu` proven against live AEAT (T-010) — ported, not imported (the PoC is throwaway).

## Approach

Stand up a self-contained, versioned `compliance` Django app whose public API is
the only surface callers touch (AD-2). Internally split: `records.py` (XML
builders + `huella`, adapted from the T-010-proven PoC and fed from T-012
`Invoice`/`calc` instead of hard-coded values), `signing.py` (XAdES enveloped
signature over the built element using `certificates` key material), `validation.py`
(legal-field gate), and `services.py` (the transactional orchestration that
locks the issuer's chain tail, computes the chained `huella`, signs, and persists
a `VerifactuRecord`). Chaining mirrors the T-012 numbering pattern — one
`transaction.atomic()` + row-lock so the chain can't fork. The module stops at a
persisted, signed record; submission is T-014's adapter behind AD-3.

## Structure

**Add:**
- `compliance/__init__.py` — public API re-exports + `MODULE_VERSION`
- `compliance/apps.py`, `compliance/models.py` (`VerifactuRecord`), `compliance/migrations/0001_initial.py`
- `compliance/records.py` — `RegistroAlta`/`RegistroAnulación` builders + `compute_huella` (ported from PoC)
- `compliance/signing.py` — XAdES enveloped signing + verification helper
- `compliance/validation.py` — legal-field gate
- `compliance/services.py` — `generate_alta` / `generate_anulacion` (transactional chain + persist)
- `compliance/tests/` — validation, alta+XSD, huella, chain, signing, annulment
- `compliance/tests/fixtures/` — self-signed test certificate + a vendored copy of the Verifactu XSD for local validation

**Modify:**
- `config/settings.py` — register `compliance` in `INSTALLED_APPS`
- `requirements.txt` — add `lxml` + the pinned XAdES/XML-DSig library

**Do not touch:**
- `invoicing/models.py`, `invoicing/services.py` — issued invoices are immutable (T-012); this module reads them
- `certificates/crypto.py`, `certificates/models.py` — cert storage/encryption is T-011; consume only via `certificates.services`
- `poc/aeat-preproduccion/` — throwaway PoC; port logic, don't import (it is deleted per T-010 DD1)
- AEAT SOAP submission / transport — T-014 (AD-3 adapter)

## Operations

- [x] Scaffold the `compliance` app: `apps.py`, `__init__.py` exposing `MODULE_VERSION` + public API stubs, the `VerifactuRecord` model + initial migration; register it in `config/settings.py`.
- [x] Implement `validation.py` — the legal-field gate that rejects an invoice missing a mandatory Verifactu field (issuer NIF, recipient name/taxid, ≥1 line, totals, issue date), persisting nothing on failure.
- [x] Implement `records.py` — port `compute_huella` + the `RegistroAlta` builder from the PoC, fed from the invoice and `invoicing.calc` rate groups (one `DetalleDesglose` per IVA rate); add the `RegistroAnulación` builder.
- [x] Implement `signing.py` — XAdES-enveloped signature over a built record using `certificates.services.get_cert_material`, plus a verify helper; add `lxml` + the signing library to `requirements.txt`. *(signxml `XAdESSigner`/`XAdESVerifier`; signature verifies + fails on tamper — 3 tests green incl. end-to-end via `signer_for_user` + the cert store.)*
- [x] Implement `services.py` `generate_alta` — one `transaction.atomic()` that row-locks the issuer's chain tail, computes the chained `huella` (or `PrimerRegistro=S`), signs, and persists the `VerifactuRecord`. *(chain + persist done; signing wired via an injectable `signer` callable — the XAdES signer arrives with the box above.)*
- [x] Implement `services.py` `generate_anulacion` — build the chained, signed `RegistroAnulación` referencing an existing record's `IDFactura` and persist it as a `anulacion` record (UC-005).
- [x] (tester) Add the `compliance` test suite covering all seven requirements — validation rejection, alta XSD-conformance + per-group Desglose, huella reproduction, chain linkage + fork-safety (Postgres-gated race like T-012), signature verify/tamper, annulment reference — and run the full suite green. *(17 compliance tests green covering req 1–7; req-3 XSD-conformance validates the full `RegFactu` envelope against the vendored AEAT schemas for both single-rate and 21%+exempt; Postgres race present + skipped on SQLite like T-012. Full suite 54 green, 2 Postgres-gated skips.)*

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/architecture-notebook.md` §3 (AD-2 versioned module, AD-3 boundary, AD-6 transactional store), §4 (module map)
- `invoicing/` — the T-012 patterns this mirrors (pure-function core, transactional row-lock numbering, Postgres-gated concurrency test)

## Safeguards

- **No-go zones.** Must not submit to / call the AEAT (T-014). Must not mutate an
  issued `Invoice` (T-012 immutability). Must not read or store certificate
  ciphertext directly — only via `certificates.services` (T-011 least-privilege).
- **Secret handling.** The decrypted private key is used only inside the signing
  call, never logged, never written to the repo, never placed in agent context
  (mirrors T-010 DD2). Tests use a self-signed fixture cert, not the founder's real cert.
- **Chain integrity.** A persisted `VerifactuRecord` is append-only; never
  re-chained, re-huellaed, or deleted. Chain generation is transactional so it
  cannot fork (AD-6/Q-1).
- **Module boundary.** Every Verifactu rule stays behind the `compliance` public
  API (AD-2/R-01) — no rule leaks into caller code.
- **Reversibility.** Net-new app + two additive deps; back out = drop the app
  from `INSTALLED_APPS` + revert the migration. No data migration of existing tables.
- See `docs/architecture-notebook.md` §3 for the decisions; do not restate them here.

## Success Measures

**n/a — internal compliance core, not yet user-facing.** Submission (and thus any
"first-submission acceptance rate", Q-2 ≥99%) arrives with T-014; there is no live
funnel to move on release. The falsifiable, deterministic expectation for this task
is **read back in CI on every run**, not on a release date: every generated
`RegistroAlta` validates against the published Verifactu XSD, every `huella`
reproduces the AEAT spec concatenation bit-for-bit, and every signature verifies
(and fails on tamper) — asserted by the `compliance` suite. Revisit and attach a
release-window measure when T-014 makes acceptance observable.

## Rollout

**Not flagged — n/a.** Net-new internal module with no user-facing surface live at
this phase (nothing is submitted until T-014). A flag would guard behavior no user
can reach yet, so it adds no safety; there is no flag-removal follow-up to enqueue.
When submission ships (T-014), gating the user-visible "report to AEAT" path is that
task's Rollout concern.

## Verification

- `python manage.py test compliance` is green; the Postgres-gated chain-race test
  runs on PostgreSQL and is documented-skipped on SQLite (mirrors T-012 DD6).
- A generated `RegistroAlta` passes `validate_local` against the vendored Verifactu XSD.
- `compute_huella` output matches the T-010-proven concatenation for a known input.
- A signed record verifies against its certificate and fails verification after a
  one-byte mutation.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-013/plan.md` exits 0.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅.

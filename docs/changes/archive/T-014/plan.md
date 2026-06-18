---
id: T-014
title: AEAT submission adapter behind AD-3 interface
status: done
priority: high
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-011, T-013]
blocks: [T-017, T-018]
touches: [submission/, config/settings.py, requirements.txt]
last-synced: ""
---

# T-014 — AEAT submission adapter behind AD-3 interface

## Story

> **As an** autónomo issuing an invoice
> **I want** the Verifactu record sent to the AEAT and its outcome recorded
> **So that** my invoice is legally reported without me filing it by hand, and I
> can see whether the tax authority accepted or rejected it.

INVEST check:
✅ Independent (consumes the T-013 record + T-011 cert through their interfaces) ·
✅ Negotiable (retry policy / pending handling are tunable) ·
✅ Valuable (realizes UC-002, the core compliance promise) ·
✅ Estimable (PoC already proved the transport) ·
✅ Small (one adapter behind one interface; no async broker) ·
✅ Testable (parse outcomes + retry behaviour are unit-checkable, transport is
cert-gated/integration).

## Analysis Context

- **Domain.** AD-3 — the AEAT VERI\*FACTU submission gateway. It takes a
  signed `VerifactuRecord` (produced by the AD-2 compliance module, T-013),
  sends it to the AEAT over mutual-TLS SOAP using the user's stored qualified
  certificate (T-011), and records the per-record outcome. Realizes UC-002.
- **Scope boundaries.** This task does **not**: generate or sign the record
  (AD-2 / T-013 owns that — the adapter submits `record.xml` as-is); manage
  certificates (T-011); track invoice-level status (issued/sent is T-018);
  build corrective/annulment submission flows beyond reusing the same gateway
  (T-017); introduce an async task broker (Celery/queue). "Queue + notify"
  (UC-002 alt 2a) is realized as a persisted `pending` attempt a later retry
  picks up — not a message-broker.
- **Definition of done.** A `SubmissionGateway` interface exists with one direct
  AEAT adapter behind it; calling `services.submit_record(record)` performs the
  mTLS SOAP submission, parses the AEAT response, and persists a
  `SubmissionAttempt` (accepted+CSV / rejected+code / pending) linked to the
  record; transport failures retry then degrade to `pending`; the AEAT
  environment is config-selected and defaults to preproducción; the unit suite
  (outcome parsing + retry + flag + least-privilege) is green.

Open questions were classified (Ambiguity Gate); none change scope, so all are
recorded as vetoable assumptions rather than raised as blocking input-requests:

> **Assumption:** The submission outcome is stored in a new `SubmissionAttempt`
> model keyed to the `VerifactuRecord` (not mutated onto `Invoice`, which is
> immutable once issued, nor onto the record, which is append-only). *(Vetoable at review.)*
> **Assumption:** Transport failures (timeout / connection reset / HTTP 5xx)
> retry up to 3 times with exponential backoff; **business rejections
> (`Incorrecto`) are never retried** — they need a corrected record. On
> persistent transport failure the attempt persists as `pending`. *(Vetoable at review.)*
> **Assumption:** The `SistemaInformatico` (SIF) producer block stays as the
> issuer identity already embedded in `record.xml` by T-013 (DD10) — XSD-valid
> and what preproducción accepted. Setting FacturaSimple's own SaaS fiscal
> identity as SIF producer is a pre-production launch task, out of scope here. *(Vetoable at review.)*
> **Assumption:** Submission is gated by a config-read kill-switch
> (`AEAT_SUBMISSION_ENABLED`, default off) so an external tax-authority call is
> never made by accident in local/CI. *(Vetoable at review.)*

## Requirements

1. A `SubmissionGateway` interface defines a single `submit(record) -> SubmissionOutcome`
   operation; the direct AEAT adapter implements it and callers depend only on
   the interface (AD-3 — a gateway adapter can later be swapped in unchanged).
   - **Given** the `submission.services.submit_record` orchestration **When** it
     submits a record **Then** it calls only the `SubmissionGateway` interface,
     never an adapter-specific symbol, so a second adapter satisfies the same call site.
2. The adapter establishes the AEAT mTLS session using the owner's certificate
   obtained **only** through `certificates.services.get_cert_material` — the
   sole sanctioned plaintext path (T-011 least-privilege).
   - **Given** an issued record whose owner has a stored certificate **When** the
     adapter opens its session **Then** the PKCS#12 material comes from
     `get_cert_material(owner)` and no code path reads `certificates.crypto.decrypt` directly.
   - **Given** an owner with no stored certificate **When** submission is attempted
     **Then** `CertificateNotConfigured` propagates and no SOAP call is made.
3. The adapter wraps the record's signed XML in the VERI\*FACTU SOAP envelope,
   POSTs it to the configured AEAT endpoint, and parses the response into a
   structured outcome carrying estado (`Correcto` / `AceptadoConErrores` /
   `Incorrecto`), the AEAT error code (when present) and the `CSV`.
   - **Given** an AEAT response with `EstadoRegistro=Correcto` and a `CSV` **When**
     the adapter parses it **Then** the outcome is `accepted` with that CSV stored.
   - **Given** an AEAT response with `EstadoRegistro=Incorrecto` and a
     `CodigoErrorRegistro` **When** parsed **Then** the outcome is `rejected`
     carrying that code and its description.
4. Each submission persists a `SubmissionAttempt` linked to the `VerifactuRecord`,
   recording status, AEAT code/CSV, an attempt timestamp, and a count of transport
   retries — without mutating the record or the invoice.
   - **Given** an accepted submission **When** `submit_record` returns **Then** a
     `SubmissionAttempt` row exists with `status=accepted`, the CSV populated, and
     the linked record/invoice rows unchanged.
5. Transport failures (timeout, connection error, HTTP ≥ 500) retry per the bounded
   policy; on persistent failure the attempt is stored `pending` (never lost) and
   a business `Incorrecto` rejection is **not** retried.
   - **Given** the AEAT endpoint raises a connection timeout on every attempt
     **When** `submit_record` runs **Then** it makes exactly the configured number
     of attempts and persists one `SubmissionAttempt` with `status=pending`.
   - **Given** the AEAT returns `Incorrecto` on the first attempt **When**
     `submit_record` runs **Then** it does not retry and stores `status=rejected`.
6. The AEAT endpoint/environment is resolved from settings (env-var), defaults to
   **preproducción**, and submission only runs when `AEAT_SUBMISSION_ENABLED` is
   true — so production is never reached by accident.
   - **Given** `AEAT_SUBMISSION_ENABLED` is unset/false **When** `submit_record`
     is called **Then** it short-circuits without opening a session and records no
     accepted/rejected attempt (returns a disabled/skipped outcome).
   - **Given** no `AEAT_ENV`/endpoint override **When** the adapter resolves its
     target **Then** it points at the preproducción address, not production.

## Behavior Delta

**Added** — behavior that did not exist before:
- The system now submits issued invoices' Verifactu records to the AEAT and
  records the accepted/rejected/pending outcome — realizing
  `docs/use-cases/UC-002-submit-invoice-to-aeat.md` (basic flow + alt-flows 3a/2a),
  which was approved but had **no runtime behavior** before this task.

**Modified** — n/a (UC-002 is realized as written; its flow text is not changed).

**Removed** — n/a.

## Entities

- **SubmissionGateway** (new) — `submission/gateway.py` (interface + `SubmissionOutcome`).
- **AeatDirectAdapter** (new) — `submission/aeat_direct.py` (the AD-3 v1 adapter).
- **SubmissionAttempt** (new) — `submission/models.py` (per-record outcome row).
- **submit_record** (new) — `submission/services.py` (orchestration + retry policy).
- **VerifactuRecord** (read-only) — `compliance/models.py` (`.xml`, `.invoice`, owner link).
- **CertMaterial / get_cert_material** (read-only) — `certificates/services.py` (mTLS material).
- **AEAT_\* settings** (new) — `config/settings.py` (env, endpoint, enable flag, retry count).

## Approach

Add a thin `submission` app that is the AD-3 boundary: a `SubmissionGateway`
interface with one `AeatDirectAdapter` behind it, mirroring how AD-2 isolates
compliance behind a versioned module. The adapter **productionizes** the proven
T-010 PoC (mTLS `.p12` session, hand-built SOAP envelope, response parse) —
 porting that logic into tested module code, not importing the throwaway PoC.
Cert material flows in through `certificates.services` and the record XML through
`compliance` — the adapter owns neither. Orchestration (`services.submit_record`)
holds the retry/pending policy and persists a `SubmissionAttempt`, keeping the
adapter a pure transport. A second (gateway) adapter could later satisfy the same
interface without touching call sites — R-03's pre-agreed fallback seam.

## Structure

**Add:**
- `submission/__init__.py`, `submission/apps.py`
- `submission/gateway.py` — `SubmissionGateway` ABC + `SubmissionOutcome` dataclass + status enum
- `submission/aeat_direct.py` — `AeatDirectAdapter` (mTLS session, SOAP envelope, response parse)
- `submission/services.py` — `submit_record(record)` orchestration + bounded retry → pending
- `submission/models.py` — `SubmissionAttempt`
- `submission/migrations/0001_initial.py`
- `submission/tests/` — `test_gateway.py`, `test_aeat_direct.py`, `test_services.py`, `factories.py`

**Modify:**
- `config/settings.py` — register `submission` app; add `AEAT_ENV`, `AEAT_ENDPOINT`,
  `AEAT_SUBMISSION_ENABLED`, `AEAT_SUBMISSION_MAX_RETRIES` (env-read).
- `requirements.txt` — add `requests-pkcs12` (PKCS#12 mutual-TLS session); lxml
  (already pinned) parses the response.

**Do not touch:**
- `compliance/services.py`, `compliance/records.py` — record generation/signing is
  AD-2's job; the adapter submits `record.xml` verbatim.
- `invoicing/models.py` (`Invoice`) — immutable once issued; invoice-level status is T-018.
- `certificates/crypto.py` — cert plaintext only via `certificates.services.get_cert_material`.
- `poc/aeat-preproduccion/` — throwaway PoC; port its logic into the app, never import it.

## Operations

- [x] Scaffold the `submission` app (`__init__`, `apps`), register it in
      `config/settings.py`, and add the `AEAT_*` env-read settings
      (`AEAT_ENV` default preproducción, `AEAT_ENDPOINT`, `AEAT_SUBMISSION_ENABLED`
      default off, `AEAT_SUBMISSION_MAX_RETRIES` default 3).
- [x] Define the AD-3 boundary in `submission/gateway.py`: a `SubmissionGateway`
      ABC with `submit(record) -> SubmissionOutcome`, the `SubmissionOutcome`
      dataclass (estado/status, aeat_code, csv, raw), and a status enum
      (accepted / rejected / pending / disabled).
- [x] Implement `AeatDirectAdapter` in `submission/aeat_direct.py` — open the
      mTLS session from `get_cert_material(owner)`, build the SOAP envelope around
      `record.xml`, POST to the resolved endpoint, and parse estado/code/CSV
      (porting the PoC's envelope + parse).
- [x] Add the `SubmissionAttempt` model + migration, then implement
      `submission/services.submit_record(record)` — short-circuit when the flag is
      off, call the gateway, persist the outcome, and apply the bounded
      transport-retry → `pending` policy (no retry on `Incorrecto`).
- [x] (tester) Unit-test the suite with the AEAT transport stubbed: outcome
      parsing for Correcto/AceptadoConErrores/Incorrecto, retry→pending on
      transport failure, no-retry on rejection, flag-off short-circuit,
      cert-plaintext-only-via-service, and gateway-interface conformance.
- [x] (tester) Run `python manage.py makemigrations --check` + the full test
      suite green; provide a cert-gated preproducción smoke path that skips
      cleanly when `AEAT_*` env is absent.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `compliance/services.py` + `certificates/services.py` — the interface-only
  consumption pattern (lazy public surface, single sanctioned plaintext path) this
  app mirrors.
- `docs/architecture-notebook.md` §AD-3 (submission interface), §AD-4 (EU residency,
  RGPD surface) — referenced, not restated.

## Safeguards

- **Token / size budget.** New app stays small — interface + one adapter +
  orchestration + model (~4 source files); no async broker, no new datastore.
- **Reversibility.** `AEAT_SUBMISSION_ENABLED=false` is the kill-switch: turning
  it off stops all outbound AEAT calls; records still generate, submission defers
  to `pending`. The app is additive — removing it leaves T-012/T-013 intact.
- **No-go zones.** Do not mutate `VerifactuRecord` or `Invoice` (both append-only
  on identity). Do not read certificate plaintext outside `certificates.services`.
  Do not point at the AEAT production endpoint without an explicit `AEAT_ENV`/endpoint override.
- **RGPD.** Never log NIF, recipient name, certificate plaintext, or CSV in clear
  application logs (AD-4) — store the CSV in the row, not the log stream.
- **Correctness invariant.** A business `Incorrecto` is never auto-retried (it
  would re-submit a record the AEAT already judged invalid).

## Success Measures

> We expect **≥ 99% of first submissions to be accepted** (estado
> `Correcto` or `AceptadoConErrores`, not `Incorrecto`) — Q-2 — measured over the
> preproducción integration corpus plus the **first 2 weeks** of beta submissions.
> Instrumentation: count of `SubmissionAttempt` rows grouped by `status`
> (`accepted` / `rejected` / `pending`). Read-back: **2 weeks after the
> submission flag is enabled in beta**.

## Rollout

- **Flagged?** **Yes** — submission makes an irreversible call to an external tax
  authority, so a config-read kill-switch is real safety (not ceremony): it lets
  us stop all outbound submissions without a redeploy (KB *Develop Backout Plan*).
- **Flag name:** `AEAT_SUBMISSION_ENABLED` (env-var, config-read at startup).
- **Default state per environment:** **local** = false (no cert/endpoint; CI never
  calls AEAT); **production** = false until launch readiness (cert onboarding +
  SIF producer identity set), then flipped on for beta.
- **Kill-switch behavior:** turning it off short-circuits `submit_record` before
  any session opens — in-flight invoices keep their generated records and simply
  hold no accepted/pending attempt until it is re-enabled; no data is lost or corrupted.
- **Flag-removal follow-up:** once submission is GA and the adapter is trusted
  post-beta, remove `AEAT_SUBMISSION_ENABLED` and make submission unconditional
  (enqueued into the roadmap by `/openup-complete-task`).

## Verification

- `python manage.py makemigrations --check --dry-run` passes (migration committed).
- `python manage.py test submission` green — covers outcome parsing, retry→pending,
  no-retry-on-rejection, flag-off short-circuit, cert-only-via-service, interface conformance.
- Grep confirms no call site outside `submission/aeat_direct.py` resolves an
  adapter-specific symbol, and no submission code imports `certificates.crypto`.
- Manual: cert-gated preproducción smoke submits one record and records its CSV.
- Grade this spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

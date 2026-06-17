---
id: T-010
title: AEAT preproducción submission PoC (3 proofs)
status: done   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 2 sessions   # time-boxed PoC; exceeding the box triggers the AD-3 gateway fallback
plan: docs/roadmap.md#construction
depends-on: [T-006, T-007]
blocks: [T-011, T-013, T-014]
touches:
  - poc/aeat-preproduccion/
  - docs/changes/T-010/
  - docs/architecture-notebook.md   # AD-3 §3 running-proof annotation (Operations box)
  - docs/input-requests/            # resume: answer + archive the access request
last-synced: ""
---

# T-010 — AEAT preproducción submission PoC (3 proofs)

## Story

> **As** the FacturaSimple founder/developer
> **I want** a running proof that we can authenticate, submit a conformant
> Verifactu `alta` record, and chain its `huella` against the AEAT
> `preproducción` sandbox
> **So that** the BUILD-direct AD-3 decision is backed by a *running* proof and
> residual R-03 (the highest live technical risk) collapses from "high" to
> "managed" before broad Construction build begins.

INVEST check:
✅ Independent (self-contained PoC; predates the app) · ✅ Negotiable (proof depth within the time box) · ✅ Valuable (gates the build-vs-buy fallback, burns down R-03) · ✅ Estimable (3 named proofs, fixed sandbox) · ✅ Small (transport + auth only — record gen already designed in AD-2) · ✅ Testable (each proof has an observable sandbox outcome)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** AEAT **VERI\*FACTU sending-mode** integration (RD 1007/2023 / Orden
  HAC/1177/2024): a SOAP web service, XML against published XSD, qualified-
  certificate (client-cert TLS) auth, with hash-chained billing records. Resolves
  the *running-proof* half of AD-3 (the analysis half landed in T-007). Source of
  truth for the three proofs: `docs/changes/archive/T-007/design.md §2`.
- **Scope boundaries.** This is a **throwaway feasibility PoC**, NOT production
  code. It does **not** build: the versioned compliance/Verifactu module (T-013),
  the production submission adapter behind AD-3 (T-014), the certificate
  store/onboarding (T-011), the invoicing core (T-012), or any UI/persistence. It
  proves the transport + auth + hash-chain mechanics work against the real sandbox,
  then records the outcome. No `anulación`/error-recovery breadth beyond the two
  chained records proof 3 needs. común-territory Verifactu only — **no TicketBAI**
  (AD-3 scope, N-6).
- **Definition of done.** The three proofs (§Requirements R1–R3) have each been
  *attempted* against AEAT `preproducción` and their outcome — pass, or
  fail-with-blocker — is recorded in `docs/changes/T-010/design.md`. A clear
  PASS/FAIL verdict on each, plus the consequent AD-3 call (proceed with BUILD, or
  trigger the gateway-fallback escalation), is the deliverable. **Clearing all
  three is the success path, but an honest, evidenced FAIL that triggers the
  fallback is also a complete, valuable outcome** — the gate working as designed.

> **Assumption:** A certificate usable against AEAT `preproducción` is obtainable
> by the developer running the PoC (an FNMT test certificate, or the founder's own
> qualified cert exercised against the sandbox). The PoC code is identical either
> way. *(Vetoable at review — if no cert can be obtained, proof R1 fails closed and
> the time box / fallback applies.)*
> **Assumption:** PoC time box = the 2-session estimate. If the three proofs have
> not cleared by then, the PoC stops and records the blocker, which **triggers the
> AD-3 gateway-fallback decision** (a founder call via `/openup-request-input`) —
> it does not silently extend. *(Vetoable at review.)*
> **Assumption:** PoC code lives self-contained under `poc/aeat-preproduccion/`
> (the repo is greenfield; the Django app arrives with T-012), and is explicitly
> **not** carried forward as production code. *(Vetoable at review.)*
> **Assumption:** Stack per AD-5 — Python with `zeep` (SOAP), `signxml`
> (XAdES/XML-DSig), `lxml`/`cryptography` (XML + cert/TLS), stdlib `hashlib` for
> the `huella`. *(Vetoable at review.)*

## Requirements

1. **Certificate auth (Proof 1).** The PoC authenticates to the AEAT
   `preproducción` VERI\*FACTU web service using a qualified certificate over
   client-certificate TLS and receives a service-level (non-auth-rejected)
   response.
   - **Given** a certificate provisioned for `preproducción` and the published
     sandbox endpoint, **When** the PoC opens a client-cert TLS session and issues
     a service call, **Then** the AEAT service accepts the TLS/certificate
     handshake and returns a SOAP response (not a TLS/auth rejection), and the
     outcome is logged.
2. **XSD-conformant `alta` submission (Proof 2).** The PoC generates one Verifactu
   `registro de facturación de alta`, validates it against the published XSD
   *before* sending, submits it, and the AEAT returns a per-record outcome of
   `Correcto` or `AceptadoConErrores`.
   - **Given** an `alta` record built from a sample invoice and validated locally
     against the AEAT XSD, **When** the PoC submits it to `preproducción`, **Then**
     the response carries a per-record status of `Correcto` or `AceptadoConErrores`
     (i.e. schema-accepted — **not** `Incorrecto` for a structural/XSD reason), and
     the status + any AEAT error codes are recorded.
3. **`huella` hash-chain (Proof 3).** The PoC computes the `huella` per the AEAT
   spec and submits two chained records (an `alta`, then a second `alta` or an
   `anulación`) where the second carries the prior record's `huella`, and AEAT
   accepts the chain.
   - **Given** a first record accepted in Proof 2 with a known `huella`, **When**
     the PoC builds a second record embedding that `huella` as its predecessor link
     and submits it, **Then** AEAT returns `Correcto`/`AceptadoConErrores` for the
     second record with **no** hash-chain (`huella`/encadenamiento) error code, and
     both records' `huella` values are recorded.
4. **Time-box gate honored.** Each proof ends in an explicit recorded verdict, and
   a proof that cannot clear within the time box triggers the AD-3 gateway-fallback
   escalation rather than open-ended continuation.
   - **Given** a proof blocked by a defect that cannot be resolved within the
     2-session box, **When** the box is reached, **Then** the PoC records the
     specific blocker in `design.md` and raises a founder decision via
     `/openup-request-input` for the AD-3 gateway fallback — the lane does not
     silently extend.

## Behavior Delta

`n/a — all Added.` This is a throwaway feasibility PoC: it adds a proof harness
and a recorded outcome but changes **no** shipped Ring-1 product behavior. It
*validates the feasibility of* UC-002 (`docs/use-cases/UC-002-submit-invoice-to-aeat.md`)
without altering that use case; the production submission behavior is delivered
later by T-013/T-014. No Modified/Removed entries.

## Entities

- **AEAT VERI\*FACTU `preproducción` web service** (read-only / external) — SOAP
  endpoint + published WSDL/XSD; the system under proof.
- **`registro de facturación de alta`** (new, throwaway) — the Verifactu billing
  record built for proofs 2–3 — `poc/aeat-preproduccion/`.
- **`huella` hash-chain link** (new, throwaway) — the per-record fingerprint and
  predecessor reference proved in Proof 3.
- **Qualified certificate** (read-only) — supplied to the PoC for client-cert TLS;
  **never committed** (see Safeguards). Production storage is T-011, out of scope.
- **AD-3 decision** (modified) — moves from analysis-only ("BUILD, PoC-gated") to a
  *running-proof-backed* decision — `docs/architecture-notebook.md §3`.

## Approach

Build the smallest possible Python harness that exercises the real
`preproducción` endpoint end-to-end for the three named proofs, in order
(auth → conformant single submission → chained submission), so each proof builds
on the last. Use the AD-5 toolchain (`zeep`, `signxml`, `lxml`/`cryptography`,
`hashlib`) against the *published* WSDL/XSD so the contract is taken from AEAT,
not guessed. Treat the harness as disposable evidence: optimize for a clear,
recorded PASS/FAIL per proof and a fast read on the AD-3 go/fallback call — not
for reuse, abstraction, or coverage breadth. Keep all secrets out of the repo.

## Structure

**Add:**
- `poc/aeat-preproduccion/` — self-contained PoC package (harness scripts for the
  three proofs; sample invoice/record fixtures; published WSDL/XSD references or a
  fetch note).
- `poc/aeat-preproduccion/README.md` — how to run the proofs (cert path via env
  var, endpoint config) and the explicit "throwaway PoC — not production code" note.
- `docs/changes/T-010/design.md` — the recorded proof outcomes (per-proof
  PASS/FAIL + evidence) and the consequent AD-3 verdict.

**Modify:**
- `docs/architecture-notebook.md` — AD-3 §3: annotate that the PoC has run and
  record the running-proof outcome (only on a clear verdict).
- `.gitignore` — ensure certificate/key material and any captured sandbox
  payloads with credentials are ignored.

**Do not touch:**
- Any production module (compliance/Verifactu T-013, submission adapter T-014,
  certificate store T-011, invoicing core T-012) — out of scope; the PoC is
  disposable and must not pre-empt those designs.
- `docs/use-cases/UC-002-*` — the PoC validates it; it does not change it.

## Operations

- [x] Scaffold `poc/aeat-preproduccion/` (deps via a venv/requirements: `zeep`,
      `signxml`, `lxml`, `cryptography`), fetch/reference the published
      `preproducción` WSDL + XSD, and add the README + `.gitignore` entries for
      cert/key material.
- [x] **Proof 1** — implement client-cert TLS auth to the `preproducción` endpoint;
      run it and record the auth outcome (handshake accepted + SOAP response, or
      blocker) in `design.md`.
- [x] **Proof 2** — build one `alta` record from a sample invoice, validate it
      locally against the XSD, submit it, and record the per-record status
      (`Correcto`/`AceptadoConErrores`/`Incorrecto` + AEAT error codes) in `design.md`.
- [x] **Proof 3** — compute the `huella`, submit a second record chained to the
      first, and record the chain-acceptance outcome (both `huella` values, any
      encadenamiento error) in `design.md`.
- [x] (analyst) Write the PoC verdict in `design.md`: per-proof PASS/FAIL with
      evidence, and the AD-3 consequence — **proceed with BUILD** (all proofs
      cleared) **or** trigger the gateway-fallback escalation via
      `/openup-request-input` (any proof blocked at the time box).
- [x] On a clear verdict, annotate AD-3 §3 of `docs/architecture-notebook.md` with
      the running-proof outcome.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/architecture-notebook.md` §3 (AD-3, AD-4, AD-5) — adapter interface intent,
  EU-residency, and the Python toolchain this PoC uses.
- `docs/changes/archive/T-007/design.md` §2 — the authoritative definition of the
  three proofs.

## Safeguards

- **Token / size budget.** Harness ≤ ~300 lines across scripts; if it grows past
  that the PoC is overreaching its proof scope.
- **Reversibility.** 2-session time box; exceeding it on a hard blocker triggers
  the AD-3 gateway-fallback decision (founder call), per Requirement 4 — back-out
  is "swap the gateway adapter behind the same AD-3 interface," already pre-agreed
  (R-03 mitigation), so no architecture rework. The PoC code is throwaway and can
  be deleted without product impact.
- **No-go zones.** No change to AD-3's *interface intent*, UC-002, or any
  production module. común-territory Verifactu only (no TicketBAI).
- **Secrets never committed.** Qualified certificates, private keys, and any
  sandbox payloads containing credentials stay out of git (env-var / local-path
  injection; `.gitignore` enforced). RGPD surface — even in `preproducción`.

> Adapter interface intent and EU-residency invariants are in
> `docs/architecture-notebook.md` §3–§5 — referenced, not restated.

## Verification

How a reviewer (human or agent) confirms the task is done:
- `poc/aeat-preproduccion/README.md` exists and documents how to run the three
  proofs; the harness runs against `preproducción` (not a mock) for each proof.
- `docs/changes/T-010/design.md` records a PASS/FAIL verdict **per proof** with
  evidence (response status, AEAT error codes, both `huella` values for Proof 3)
  and states the resulting AD-3 call.
- No certificate/key material or credentialed payload is tracked by git
  (`git ls-files | grep` clean; `.gitignore` covers the patterns).
- If any proof failed at the time box, an input-request for the AD-3 gateway
  fallback exists (or is archived as answered).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-010/plan.md`
  exits 0.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every
  criterion ✅.

## Rollout

`n/a — internal feasibility PoC, not user-facing and never shipped.` No feature
flag: there is no production code path and no users to toggle. The PoC's only
"release" is its recorded verdict feeding the AD-3 go/fallback decision.

## Success Measures

`n/a — internal feasibility PoC; no release, no user-facing behavior, nothing to
instrument post-release.` The deliverable *is* the binary proof outcome: the three
proofs each resolve to PASS or FAIL-with-blocker against `preproducción`, recorded
in `design.md`, and that record either backs the BUILD-direct AD-3 commitment or
triggers the gateway fallback. Read-back is immediate (this lane), not a future
metric window — so a deferred success measure would be a vanity metric nobody reads.

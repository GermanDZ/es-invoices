---
id: T-011
title: Secure user-certificate upload + encrypted storage
status: done
priority: high   # critical | high | medium | low
estimate: 2 sessions
plan: docs/roadmap.md#construction   # link to originating plan, if any
depends-on: [T-010]
blocks: [T-014]
touches: [certificates, config, manage.py, requirements.txt, .env.example, .gitignore]
last-synced: ""    # full git SHA of last code↔spec sync (set by /openup-sync-spec)
---

# T-011 — Secure user-certificate upload + encrypted storage

## Story

> **As an** autónomo onboarding to FacturaSimple
> **I want** to upload my own qualified AEAT certificate and have it stored securely
> **So that** the system can submit Verifactu records to the AEAT on my behalf without my certificate ever being exposed in plaintext

INVEST check:
✅ Independent — depends only on T-010 (proof) · ✅ Negotiable — scheme/validation depth are assumptions · ✅ Valuable — unlocks the whole submission path · ✅ Estimable — 2 sessions · ✅ Small — one app, one model, one crypto helper · ✅ Testable — upload/encrypt/retrieve/delete all assert observable outcomes

## Analysis Context

- **Domain.** User onboarding + secrets management. The qualified AEAT certificate
  (P12/PFX, per the T-010 PoC) is the credential that authenticates the user's
  Verifactu submissions over client-cert TLS. This task owns the *provisioning and
  at-rest protection* of that credential; it does **not** perform submission.
- **Scope boundaries.** Does NOT submit to AEAT (T-014), does NOT build Verifactu
  records (T-013), does NOT manage the broader user/account model beyond the
  certificate relationship, and does NOT validate the certificate's full qualified-CA
  trust chain (deferred — see assumption). No production secret-manager wiring beyond
  reading a configured key (infra is T-014/deploy concern).
- **Definition of done.** A logged-in user can upload a P12 + passphrase through a
  Django flow; the system validates it parses and is unexpired, stores both the
  certificate bytes and passphrase encrypted at rest in PostgreSQL, exposes an
  internal least-privilege accessor that returns decrypted material, lets the user
  replace or delete the certificate, and surfaces a "certificate configured" status.
  Plaintext certificate material never touches the DB, logs, or any export path.

> **Assumption:** T-011 bootstraps the minimal Django project skeleton (settings,
> `manage.py`, a `certificates` app) since it is the first Construction build task to
> land code; T-012 then builds the invoicing core on this skeleton. *(Vetoable at
> review — alternative is to make T-011 depend on T-012 for the scaffold.)*
> **Assumption:** At-rest protection uses AES-256-GCM envelope encryption with a key
> read from a dedicated secret (`CERT_ENCRYPTION_KEY`), distinct from Django
> `SECRET_KEY` and the DB. *(Vetoable at review.)*
> **Assumption:** The P12 passphrase is persisted (encrypted, same scheme) because the
> submission adapter (T-014) runs unattended and needs it at submit time. *(Vetoable —
> alternative is per-submission re-entry, which breaks unattended retry.)*
> **Assumption:** Certificate validation at upload = parses as PKCS#12 with the given
> passphrase + not-expired; full qualified-CA/FNMT trust-chain validation is deferred.
> *(Vetoable at review.)*

## Requirements

1. A logged-in user can upload a PKCS#12 (`.p12`/`.pfx`) certificate file together with
   its passphrase, and the system accepts it only after confirming it parses with that
   passphrase and is not expired.
   - **Given** a logged-in user with a valid, unexpired P12 and its correct passphrase
     **When** they submit the upload form **Then** the certificate is accepted and
     persisted, and the user sees a success state.
   - **Given** a P12 with a wrong passphrase or an expired certificate **When** the user
     submits the upload form **Then** the upload is rejected with a clear validation
     error and nothing is persisted.

2. Certificate bytes and passphrase are stored encrypted at rest (AES-256-GCM); plaintext
   material is never written to the database, logs, or any serialized output.
   - **Given** a certificate has been uploaded and stored **When** the underlying database
     row is inspected directly **Then** the stored certificate and passphrase fields are
     ciphertext (not the original bytes/string) and a per-record nonce is present.

3. A single internal accessor returns decrypted certificate material for a user, and it is
   the only sanctioned path to plaintext; the accessor is what the future submission
   adapter (T-014) consumes.
   - **Given** a stored certificate **When** the internal accessor is called for that user
     **Then** it returns the decrypted P12 bytes and passphrase ready for an mTLS session.
   - **Given** a user with no stored certificate **When** the accessor is called
     **Then** it raises a not-configured error rather than returning empty/plaintext-null.

4. A user can replace or delete their stored certificate; deletion removes the encrypted
   material, and account closure cascades that deletion (retention boundary).
   - **Given** a user with a stored certificate **When** they upload a new one
     **Then** the previous encrypted material is overwritten and no orphaned plaintext
     remains.
   - **Given** a user with a stored certificate **When** their account is deleted
     **Then** the certificate record is removed by cascade.

5. The user's certificate-configured status is observable so that UC-002's precondition
   ("the user's certificate is configured") can be checked before submission.
   - **Given** a user who has uploaded a valid certificate **When** their onboarding/
     configuration status is queried **Then** it reports `configured`.
   - **Given** a user who has not uploaded a certificate **When** the status is queried
     **Then** it reports `not-configured`.

6. Certificate material is stored only in the EU-resident PostgreSQL datastore (AD-6/AD-4)
   with no external sub-processor; access is least-privilege (only the accessor reads
   plaintext, never the upload/list views).
   - **Given** the storage implementation **When** the code paths that touch plaintext are
     reviewed **Then** only the internal accessor decrypts, and no view, serializer, log
     statement, or third-party call emits plaintext certificate material.

## Behavior Delta

**Added** — behavior that did not exist before (greenfield; no prior Ring-1 artifact):
- Certificate upload + validation flow (new onboarding capability).
- Encrypted-at-rest certificate storage and the internal least-privilege accessor.
- Replace / delete certificate, and certificate-configured status.

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- UC-002's precondition "The user's AEAT submission credentials/certificate are
  configured" gains a concrete fulfilling flow — `docs/use-cases/UC-002-submit-invoice-to-aeat.md §preconditions`.

**Removed** — n/a.

## Entities

- **UserCertificate** (new) — `certificates/models.py` — encrypted blob + passphrase + nonce + metadata
- **Crypto helper** (new) — `certificates/crypto.py` — AES-256-GCM encrypt/decrypt
- **Certificate accessor** (new) — `certificates/services.py` — `get_cert_material` / `certificate_status`
- **User** (read-only, Django auth) — owner FK on `UserCertificate`
- **AD-3 submission adapter** (read-only, future T-014) — consumer of the accessor

## Approach

Bootstrap a minimal Django project and a `certificates` app. Model `UserCertificate`
holds the encrypted P12 blob, encrypted passphrase, per-record nonce, and metadata
(subject, not-after) extracted at upload for status/expiry without decrypting. A thin
`crypto.py` does AES-256-GCM envelope encryption keyed from `CERT_ENCRYPTION_KEY`. The
upload view/form validates by loading the PKCS#12 via the `cryptography` library
(parse + not-expired) before encrypting and saving. All plaintext access funnels through
one `services.py` accessor so least-privilege is structural, not conventional.

## Structure

**Add:**
- `manage.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py` — minimal Django scaffold
- `certificates/models.py` — `UserCertificate`
- `certificates/crypto.py` — AES-256-GCM encrypt/decrypt helpers
- `certificates/services.py` — `get_cert_material(user)`, `certificate_status(user)`
- `certificates/forms.py`, `certificates/views.py`, `certificates/urls.py` — upload/replace/delete flow
- `certificates/migrations/0001_initial.py`
- `certificates/tests/` — validation, encryption-at-rest, accessor, delete/cascade, status
- `requirements.txt` — Django, cryptography
- `.env.example` — `CERT_ENCRYPTION_KEY`, DB settings

**Modify:**
- `docs/use-cases/UC-002-submit-invoice-to-aeat.md` — only if review wants the precondition annotated with the new flow reference (via `/openup-sync-spec`, not hand-edited here)

**Do not touch:**
- `poc/aeat-preproduccion/` — throwaway T-010 PoC; do not build on it
- Verifactu record generation / submission — T-013 / T-014 own these behind AD-3

## Operations

- [x] Bootstrap the minimal Django project skeleton (`config/`, `manage.py`, settings reading `CERT_ENCRYPTION_KEY` + Postgres) and the `certificates` app; wire `requirements.txt` and `.env.example`.
- [x] Implement `certificates/crypto.py` (AES-256-GCM encrypt/decrypt with per-record nonce) and its unit tests, including a wrong-key/tampered-ciphertext failure test.
- [x] Implement the `UserCertificate` model + migration: encrypted cert blob, encrypted passphrase, nonce, extracted subject + not-after, owner FK with cascade delete.
- [x] Implement the upload form/view: validate P12 parses with passphrase + is unexpired, then encrypt and store; reject invalid uploads with clear errors and persist nothing.
- [x] Implement `services.py` accessor (`get_cert_material`, `certificate_status`) as the sole plaintext path, plus replace/delete views.
- [x] (tester) Write the test suite covering all six requirements' scenarios — upload accept/reject, encryption-at-rest inspection, accessor (configured + not-configured), replace/delete cascade, and status — and confirm green.
- [x] (tester) Grep the code paths to confirm no view/serializer/log/third-party call emits plaintext certificate material (least-privilege check).

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, PR size, logging
- `docs/project-config.yaml` — project context + rule "Any auth-touching task must cite the compliance control it affects" (cited: R-06 mitigation — encryption at rest, least-privilege access, documented retention)
- `docs/architecture-notebook.md` — AD-3 (submission interface), AD-4 (EU residency), AD-5 (Python/Django), AD-6 (PostgreSQL)

## Safeguards

- **Compliance control (R-06).** This task implements the R-06 mitigations: encryption
  at rest, least-privilege access, EU residency, documented retention. See
  `docs/risk-list.md` R-06.
- **Token / size budget.** Crypto helper ≤ ~80 lines; PR target < 400 lines per
  `conventions.md`.
- **Reversibility.** Pure additive — new app + scaffold; back out by dropping the
  `certificates` migration and app. No existing behavior depends on it yet.
- **No-go zones.** Plaintext certificate material must never reach the DB, logs, error
  messages, serializers, or any third party. No certificate storage outside EU Postgres.
  Do not validate against AEAT live endpoints (T-014 scope).
- **Retention.** Certificate material is deleted on user replacement and on account
  closure (cascade); document this as the retention boundary for the pre-launch RGPD
  checklist (R-06 carry-forward).

## Verification

- `python manage.py test certificates` passes (all six requirements' scenarios green).
- Direct DB inspection of a stored row shows ciphertext + nonce, never plaintext.
- Grep confirms the single decryption path; no plaintext in views/logs/serializers.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-011/plan.md` exits 0.

## Success Measures

n/a — internal security/onboarding capability with no user-facing metric yet (no UI
funnel or billing surface live at this phase). The checkable expectation is the
verification suite above: encryption-at-rest and least-privilege are asserted by tests,
not by a post-release metric. *(Reason must survive review; revisit when onboarding ships
to beta and a "certificate-configured rate" becomes measurable.)*

## Rollout

**Flagged?** No. The certificate-upload flow is net-new and reaches no user until the
onboarding UI and the submission path (T-014) ship; there is no existing behavior to
guard and no live traffic to toggle, so a flag would add ceremony without safety. The
capability is gated naturally by being unreleased. When onboarding goes to beta, exposure
is controlled by environment/account access, not a feature flag. *(Vetoable at review; if
T-014 lands before onboarding is ready, gate the upload UI by a simple settings toggle
rather than a full flag system.)*

# T-011 Handoff — Secure user-certificate upload + encrypted storage

**Status:** in-progress · **Branch:** feat/T-011-cert-upload-storage · **For:** next developer/session
**Last commit:** (WIP committed on branch) — see `git log feat/T-011-cert-upload-storage`

Operations 1–2 of 7 are done and green. The spec (`plan.md`, status `ready`) and
design decisions (`design.md`) are authoritative — read them first. Resume from
Operation 3 (the first unchecked box). The iteration is active (worktree
`../es-invoices-T-011`, lease + `.openup/state.json` in place); do NOT re-run
`/openup-start-iteration`.

## 1. Acceptance criteria
> The six requirements in plan.md. Each carries Given/When/Then scenarios there.
- [x] R1 — Upload a P12/PFX + passphrase; accepted only if it parses with that passphrase and is unexpired. *(crypto+validation primitive ready; upload form/view is Operation 4)*
- [x] R2 — Cert bytes + passphrase stored encrypted (AES-256-GCM), never plaintext in DB/logs/output. *(crypto.py done + tested; model storage is Operation 3)*
- [ ] R3 — A single internal accessor returns decrypted material; raises not-configured when absent. *(Operation 5)*
- [ ] R4 — Replace/delete cert; deletion removes encrypted material; account-closure cascade. *(Operations 3+5)*
- [ ] R5 — Certificate-configured status observable for the UC-002 precondition. *(Operation 5)*
- [ ] R6 — EU-Postgres-only storage, least-privilege (only the accessor decrypts). *(Operation 7 grep verifies)*

## 2. How to exercise it (test cases)
> From the worktree `../es-invoices-T-011`, with the venv active.
1. `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt` → installs Django 5.2 + cryptography 49 + psycopg.
2. `. .venv/bin/activate && python manage.py check` → "System check identified no issues".
3. `python manage.py test certificates.tests.test_crypto -v2` → 10 tests pass (round-trip, fresh nonce, tamper→InvalidTag, wrong-key→InvalidTag, missing/malformed/wrong-length key→EncryptionKeyError).
4. Generate an encryption key: `python -c "from certificates.crypto import generate_key; print(generate_key())"` → base64 32-byte key for `CERT_ENCRYPTION_KEY`.
5. After Operation 3: `python manage.py makemigrations certificates && python manage.py test certificates` → model + full suite green.

## 3. Troubleshooting
> From design.md / this session.
- **Spec write blocked by gate-edits.py on trunk** → cause: the hook treats `docs/changes/**/plan.md` as product source and requires `.openup/state.json`, which trunk lacks → fix: started the iteration first with `--plan` seeding `gates.plan_persisted`, then authored the spec inside the worktree (DD1). Framework follow-up noted in design.md: add `docs/changes/` to the gate's `EXEMPT_PREFIXES`.
- **Tests with no Postgres server** → cause: AD-6 mandates Postgres → fix: `config/settings.py` falls back to SQLite when `POSTGRES_DB` is unset, so tests run serverless; encryption-at-rest is storage-engine independent (DD2).
- **CERT_ENCRYPTION_KEY** must base64-decode to exactly 32 bytes or `crypto._load_key()` raises `EncryptionKeyError`; tests inject keys via `override_settings`.

## 4. Open questions
> Remaining work + decisions for the next owner. All four spec Assumptions are vetoable at review.
- Operations 3–7 remain: `UserCertificate` model + migration (encrypted cert blob + encrypted passphrase + per-field nonce + extracted subject/not-after + owner FK cascade); upload form/view with parse+expiry validation; `services.py` accessor (`get_cert_material`, `certificate_status`) + replace/delete views; full test suite for R1–R6 scenarios; least-privilege grep (Operation 7).
- Confirm the spec Assumptions at review: T-011 owns the Django bootstrap (vs deferring to T-012); AES-256-GCM + dedicated key; passphrase persisted encrypted for unattended T-014 submission; validation depth = parse + not-expired (full qualified-CA trust-chain deferred).
- `config/urls.py` includes `certificates.urls`, currently a stub with empty urlpatterns — Operation 5 wires the routes.

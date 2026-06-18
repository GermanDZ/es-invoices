# T-011 — Design decisions (in-flight)

## DD1 — Spec authored on the task branch, not trunk
The `gate-edits.py` hook treats any non-exempt repo path (including
`docs/changes/**/plan.md`) as product source and blocks writes when no
`.openup/state.json` exists. Trunk has no state, so the openup-next *promote*
path (create-task-spec **then** start-iteration) cannot write the spec on trunk.
Resolution (operator decision): reverse the order — `start-iteration` first with
`--plan docs/changes/T-011/plan.md` seeding `gates.plan_persisted`, which lets
the gate permit authoring the spec inside the worktree; it merges to trunk at
`/openup-complete-task`. Follow-up worth raising to the framework: add
`docs/changes/` to the gate's `EXEMPT_PREFIXES` (a task spec is a plan, not
product source) so the documented promote flow works as written.

## DD2 — SQLite fallback for local/test, PostgreSQL in deployed envs
AD-6 mandates PostgreSQL. `config/settings.py` uses Postgres when `POSTGRES_DB`
is set, else falls back to SQLite so the test suite and local runs need no DB
server. The encryption-at-rest behaviour (requirement 2) is storage-engine
independent — ciphertext is held in the model field regardless of backend — so
SQLite-backed tests still exercise the real security property.

## DD3 — Encryption scheme
AES-256-GCM (`certificates/crypto.py`), key from `CERT_ENCRYPTION_KEY`
(base64-encoded 32 bytes), distinct from `SECRET_KEY`. Fresh 96-bit nonce per
`encrypt()`; GCM auth tag makes wrong-key/tamper fail with `InvalidTag`. The
module is the sole key holder; `certificates/services.py` (Operation 5) will be
the sole plaintext accessor (least-privilege, requirements 3 & 6).

## DD4 — Passphrase persisted encrypted
The P12 passphrase is stored encrypted (same scheme) alongside the cert blob so
the T-014 submission adapter can run unattended (spec Assumption). Both the cert
bytes and the passphrase are separate encrypted columns on `UserCertificate`,
each with its own nonce.

## Progress
- Operations 1 (scaffold) and 2 (crypto + 10 unit tests) complete and green
  (`python manage.py test certificates.tests.test_crypto` → 10 passed; `manage.py
  check` clean).
- Operations 3–7 (model+migration, upload view/form, services accessor +
  replace/delete, full test suite, least-privilege grep) remain — see handoff.

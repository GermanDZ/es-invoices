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

## DD5 — Single plaintext path via services.py
`certificates/services.py` is the sole module that encrypts into or decrypts out
of `UserCertificate`. The model is pure ciphertext storage; the form parses the
uploaded P12 (it must, to validate) and hands raw bytes to
`services.store_certificate`, which encrypts; only `services.get_cert_material`
decrypts. `tests/test_least_privilege.py` asserts this statically by scanning for
`decrypt(` call sites outside `crypto.py`/`services.py` (requirement 6 made a
test, not just a grep).

## DD6 — One active certificate per user (OneToOne + update_or_create)
`UserCertificate.owner` is a `OneToOneField(..., on_delete=CASCADE)`.
`store_certificate` uses `update_or_create`, so re-uploading overwrites in place
(no orphaned material, requirement 4) and account deletion cascades the record
away (retention boundary, R-06). Upload validation depth = parses as PKCS#12 with
the passphrase + `not_valid_after_utc` in the future; full CA trust-chain is
deferred per the spec assumption.

## Completion verification (step 1a — graded against the diff)
- ✅ **R1** — `forms.py clean()` (PKCS#12 parse + passphrase + `not_valid_after_utc`)
  + `views.upload`; tests `test_valid_upload_is_accepted_and_persisted`,
  `test_wrong_passphrase_rejected_and_nothing_persisted`, `test_garbage_file_rejected`,
  `test_expired_certificate_rejected`.
- ✅ **R2** — `UserCertificate` ciphertext `BinaryField`s + per-blob nonce;
  `services.store_certificate` encrypts; `test_stored_material_is_ciphertext`.
- ✅ **R3** — `services.get_cert_material` (sole accessor) + `CertificateNotConfigured`;
  `test_get_cert_material_round_trips`, `test_get_cert_material_not_configured_raises`.
- ✅ **R4** — `OneToOneField(on_delete=CASCADE)` + `update_or_create` + `delete_certificate`;
  `test_replace_overwrites_previous_material`, `test_account_deletion_cascades`,
  `test_delete_certificate_removes_record`.
- ✅ **R5** — `services.certificate_status`; `test_status_configured_and_not`.
- ✅ **R6** — PostgreSQL (AD-6) with SQLite test fallback (DD2); `test_only_services_decrypts`
  + grep confirm `decrypt(` is confined to `services.py`/`crypto.py`.
- **Step 1b (Success Measures):** `n/a` — internal security/onboarding capability, no
  live funnel/billing surface at this phase; the verification suite is the checkable
  expectation. No instrumentation owed. Re-visit when onboarding ships to beta.
- **Step 4a (Rollout):** not flagged → no flag-removal task enqueued.
- Full suite: `python manage.py test certificates` → **22 passed**; `manage.py check` clean.

## Progress
- Operations 1 (scaffold) and 2 (crypto + 10 unit tests) complete and green.
- Operations 3–7 complete: `UserCertificate` model + `0001_initial` migration,
  upload/replace/delete views + form (PKCS#12 parse + expiry validation),
  `services.py` accessor (`get_cert_material`, `certificate_status`,
  `delete_certificate`), the requirement-by-requirement test suite, and the
  least-privilege static check. Full suite green: `python manage.py test
  certificates` → **22 passed**; `manage.py check` clean. `git ls-files` carries
  no cert/key material; `CERT_ENCRYPTION_KEY` is read from env only.

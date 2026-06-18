# Agent Run Log — T-011 (Operations 3–7 + completion)

- **Task:** T-011 — Secure user-certificate upload + encrypted storage
- **Branch:** feat/T-011-cert-upload-storage
- **Phase:** construction · **Track:** standard · **Iteration:** 10
- **Start:** 2026-06-18T06:12:29Z · **End:** 2026-06-18T07:47:19Z

## Commits (vs trunk 1cf4a72)
- `f3e6b6d` feat(T-011): bootstrap Django scaffold + AES-256-GCM cert crypto (Ops 1-2)
- `c351033` fix(T-011): correct sync-status false 'completed' to in-progress
- `0191b1a` feat(T-011): cert model, upload/encrypt/accessor + tests (Ops 3-7)

## Files changed (this session — Ops 3–7)
- `certificates/models.py` — `UserCertificate` (OneToOne owner, ciphertext blobs + per-blob nonce, extracted metadata)
- `certificates/migrations/0001_initial.py`
- `certificates/forms.py` — PKCS#12 parse + passphrase + expiry validation
- `certificates/views.py`, `certificates/urls.py`, `certificates/templates/certificates/upload.html` — upload/delete flow
- `certificates/services.py` — sole plaintext path: store / get_cert_material / certificate_status / delete
- `certificates/tests/{factories,test_certificate,test_least_privilege}.py` — 22-test suite
- `docs/changes/T-011/{plan.md,design.md}` — ticked Ops 3–7, recorded DD5/DD6 + completion grade, expanded `touches`

## Decisions
- DD5: decryption confined to `services.py` (static test enforces `decrypt(` confinement).
- DD6: one active cert per user (`OneToOne` + `update_or_create` overwrite; account-delete cascade).
- Validation depth = parse + not-expired; full CA trust-chain deferred (spec assumption).

## Outcome
- `python manage.py test certificates` → 22 passed; `manage.py check` clean.
- All six requirements graded ✅ against the diff; Success Measures `n/a`; not flagged.
- Write-fence exit 0 (after declaring scaffold root files in `touches` + re-claim); check-docs OK (11 instances).

## Process note (recurring friction)
- The openup-next *promote* path collided again with `gate-edits.py`: trunk has no
  `.openup/state.json`, so authoring `docs/changes/T-011/plan.md` on trunk is blocked.
  This session also discovered the lane was **already started** in a worktree by a prior
  cycle (the main-repo `openup-state.py get` reads only the main checkout's state, so the
  active iteration looked absent). Framework follow-up still open (DD1): add `docs/changes/`
  to the gate's `EXEMPT_PREFIXES` so the documented promote flow works as written.

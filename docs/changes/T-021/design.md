# T-021 — in-flight design notes

Decisions made during implementation (spec Assumptions held; nothing vetoed):

- **Email as username.** `RegistrationForm.save()` calls `create_user(username=email,
  email=email, ...)` with the email lower-cased in `clean_email`. Login reuses Django's
  `AuthenticationForm` via a thin `EmailAuthenticationForm` subclass that relabels the
  `username` field to "Email" and lower-cases it in `clean_username`; since
  `username == email`, `authenticate()` needs no custom backend. No `AUTH_USER_MODEL`
  change → no destructive migration; `accounts` ships **zero models / migrations**.
- **Login/logout = built-in CBVs.** `LoginView` (with the email form + project template +
  `redirect_authenticated_user=True`) and `LogoutView` are wired in `accounts/urls.py`;
  only `register` and the gated `landing` are custom views. `?next=` handling and CSRF come
  for free from the CBV/middleware.
- **Root landing in all environments.** `path("", include("accounts.urls"))` sits outside
  the DEBUG block, so `/` resolves to the `@login_required` landing everywhere (anonymous →
  `LOGIN_URL`). The old DEBUG-only `/`→`/dev/login/` redirect was removed; the `/dev/` shim
  routes stay DEBUG-gated and untouched (Assumption 4).
- **Password validators.** Django's four defaults enabled (were `[]` during the engine-only
  phase). Weak/numeric/common passwords now rejected at registration.

## Verification
- New `accounts/tests/test_auth.py`: 12 tests, all 6 requirements covered. Tests rely on the
  runner forcing `DEBUG=False`, so `config.urls` exposes the real routes directly — no
  `ROOT_URLCONF` override (unlike the devtools shim tests).
- Full suite: **141 passed, 2 Postgres-gated skips** (129 prior + 12 new); no regression in
  `devtools`/`clients`. The `UserCertificate.not_after` naive-datetime warning is
  pre-existing (certificates fixture), unrelated to this lane.

## Requirement grade (completion, vs the actual diff)
- ✅ **R1** register → user (`username==email`), logged in, 302 landing —
  `register` view + `RegistrationForm.save`; `test_register_creates_user_logs_in_and_redirects`.
- ✅ **R2** duplicate email / mismatch / weak rejected, no user, 200 —
  `clean_email`, `clean`; 3 registration tests green.
- ✅ **R3** login by email → landing / safe `next`; bad password → 200 no session —
  `EmailAuthenticationForm` + `LoginView`; 3 login tests green.
- ✅ **R4** POST logout clears session — `LogoutView`; `test_logout_ends_session`.
- ✅ **R5** anonymous `@login_required` → 302 `LOGIN_URL?next=`; login/register public —
  `LOGIN_URL` setting; gating tests green.
- ✅ **R6** landing names user + links clients/certificate/logout —
  `landing.html`; `test_landing_shows_user_and_links`.

## Success-measure instrumentation (step 1b)
- ✅ Instrumentation = the `accounts` auth suite under `DEBUG=False` (12 tests) — exists in
  the diff and passes; binary capability gate (0 → all `@login_required` routes reachable).
  Read-back: **at this completion (2026-06-19)** — satisfied. Usage metrics belong to T-022.

## Follow-ups surfaced (not in scope)
- Email verification / password-reset-by-email — deferred (Assumption 2); future hardening
  before public launch.
- The `devtools` shim is now redundant with real login but retained intentionally for the
  fast dev loop; a future cleanup task could retire it.

# Problem note: web UI is unreachable locally — no login flow exists

**Date:** 2026-06-18
**Status:** observed (pre-iteration) — not yet scoped for delivery
**Surfaced by:** attempting to run the app locally to "fiddle with the current state of the product"

## Symptom

Starting the dev server and visiting either wired-up route 302-redirects to a
login page that does not exist, yielding a 404:

```
GET http://127.0.0.1:8000/clients/      -> 302 -> /accounts/login/?next=/clients/  -> 404
GET http://127.0.0.1:8000/certificate/  -> 302 -> /accounts/login/?next=/certificate/ -> 404
```

There is no way to reach any product page in the browser on a fresh checkout.

## Root cause

The authentication *gate* is fully built, but the authentication *door* was never
built:

- Every view in `clients/views.py` and `certificates/views.py` is
  `@login_required` and scoped to `owner=request.user` (deliberate per-owner
  isolation — a cross-owner request is a 404, not a 403 leak).
- `login_required` redirects unauthenticated users to Django's default
  `LOGIN_URL` (`/accounts/login/`).
- `config/urls.py` only registers `certificate/` and `clients/`. There is **no
  login route**, **no `django.contrib.auth.urls`**, and **no root URL**.
- `django.contrib.admin` is **not** in `INSTALLED_APPS` (`config/settings.py`),
  so there is no admin login to borrow a session from either.

Net: the only ways to obtain an authenticated session today are programmatic
(`manage.py shell` + `force_login`, or the test suite's request client). There
is no human-facing entry point.

## Secondary friction found while reproducing

- **`.env` is not auto-loaded.** `config/settings.py` reads `os.environ`
  directly with no `dotenv` loader, yet `.env.example` says "Copy to `.env`".
  Copying the file has no effect; vars must be `export`ed (or sourced) in the
  shell that launches the server. Either wire a dotenv loader or fix the
  `.env.example` guidance.
- **`CERT_ENCRYPTION_KEY` has no default** (by design — storage must never run
  unencrypted), so the certificate flow raises until it is set. Generate one
  with:
  `python -c "from certificates.crypto import generate_key; print(generate_key())"`

## Local run recipe that *does* work today (for reference)

```bash
export CERT_ENCRYPTION_KEY=$(.venv/bin/python -c "from certificates.crypto import generate_key; print(generate_key())")
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
# ...but the browser is still blocked at /accounts/login/ — see above.
```

## Options to analyze later (not decided)

1. **Wire Django admin** — add `django.contrib.admin` + `/admin/` + a superuser.
   Admin ships its own login + templates; logging in there yields a session that
   unlocks `/clients/` & `/certificate/`, and admin doubles as a CRUD surface for
   `Client` / certificate rows. Lowest effort; "admin-as-dev-tooling" framing.
2. **Build a real login flow** — register `django.contrib.auth.urls` (or a custom
   auth app) + a `registration/login.html` template + a sign-up/seed path. This is
   the actual product gap (the app is single-tenant-per-user with `owner` scoping
   but no way to *become* an owner). Larger; likely a genuine roadmap item.
3. **Dev-only shim** — a management command / dev fixture that seeds a user and a
   shortcut to authenticate locally, without committing a production login. Useful
   for fiddling but doesn't close the product gap.
4. **Add a root URL** — minor, orthogonal: there is no `/` landing page; decide
   where authenticated users land.

## Open questions for the analysis

- Is "users can log in" actually on the roadmap yet, or has every story so far
  assumed an authenticated `request.user` provided by tests? (Check whether any
  use-case in `docs/use-cases/` covers authentication / onboarding.)
- Is the product intended to be multi-user (real login + sign-up) or
  single-operator (one owner, admin-style login is enough)? This decision picks
  between options 1/3 and option 2.

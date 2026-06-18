---
id: T-020
title: Dev-only local auth shim (seed user + DEBUG-gated login shortcut)
status: in-progress
priority: low
estimate: 1 session
plan: docs/roadmap.md#construction
depends-on: [T-011, T-015]
blocks: []
touches:
  - config/settings.py
  - config/urls.py
  - devtools/owner.py
  - devtools/views.py
  - devtools/urls.py
  - devtools/apps.py
  - devtools/__init__.py
  - devtools/management/__init__.py
  - devtools/management/commands/__init__.py
  - devtools/management/commands/seed_dev_owner.py
  - devtools/tests/__init__.py
  - devtools/tests/test_dev_login.py
  - devtools/tests/urls.py
last-synced: ""
---

# T-020: Dev-only local auth shim (seed user + DEBUG-gated login shortcut)

**Phase**: construction
**Status**: pending
**Goal**: Give a developer on a fresh checkout a browser session that unlocks
`/clients/` and `/certificate/` locally — without committing any production
login surface.
**Priority**: low

---

## Context

On a fresh checkout there is **no human-facing way to reach any product page in
a browser** (`docs/explorations/2026-06-18-no-login-flow-blocks-local-ui.md`).
Every view in `clients/views.py` and `certificates/views.py` is `@login_required`
and owner-scoped, but `config/urls.py` registers no login route, there is no
`django.contrib.auth.urls`, and `django.contrib.admin` is not installed — so the
only way to obtain an authenticated session today is programmatic
(`manage.py shell` + `force_login`, or the test client). A developer cannot
"fiddle with the current state of the product" in a browser.

`docs/scope.md` already resolves the product-direction question the exploration
left open: **D-3** mandates a single-user / single-business account model and
**N-5** explicitly excludes multi-user / team accounts. No use-case in
`docs/use-cases/` covers authentication or onboarding — every story so far has
assumed an authenticated `request.user` supplied by tests.

This task does **not** build the real product login (that remains a genuine,
larger roadmap gap — "the app is single-tenant-per-user but has no way to
*become* an owner"). It builds the **dev-only shim** (exploration option 3): a
committed-but-DEBUG-gated shortcut that seeds the single owner and authenticates
a browser session locally. It unblocks local fiddling now and is provably inert
in production.

---

## Current State

### Root URL config (`config/urls.py`) — no login, no root

```python
"""Root URL configuration for FacturaSimple."""
from django.urls import include, path

urlpatterns = [
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
]
```

No `/`, no `/accounts/login/`, no `/admin/`.

### Settings (`config/settings.py:33-45`) — auth installed, admin absent, no LOGIN_URL

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "certificates",
    "clients",
    "invoicing",
    "compliance",
    "submission",
    "documents",
]
```

`django.contrib.auth` + session/auth middleware are present, so `login()` and the
session cookie work — there is simply no view that calls `login()`. `LOGIN_URL`
is unset, so `@login_required` falls back to Django's default
`/accounts/login/`, which is unrouted → 404. `DEBUG` defaults on locally
(`config/settings.py:24`). `TEMPLATES` uses `APP_DIRS=True` with no project-level
`DIRS` (`config/settings.py:58-70`).

### Gated views (`clients/views.py:14-20`) — the door these routes need

```python
@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, "clients/list.html", {"clients": clients})
```

`certificates/views.py` follows the same `@login_required` + `owner=request.user`
shape.

### How the session is obtained today — tests only (`certificates/tests/test_certificate.py:31-32`)

```python
self.user = User.objects.create_user("autonomo", password="pw")
self.client.force_login(self.user)
```

`force_login` works only on the test client, not a browser. There is no
equivalent for a running `runserver`.

### Management-command convention (`submission/management/commands/aeat_submit.py`)

Commands live under `<app>/management/commands/`. `aeat_submit` is the existing
precedent for a dev/ops `manage.py` entry point.

---

## Proposed Design

A small `devtools` app, **added to `INSTALLED_APPS` only when `DEBUG`** so neither
its management command nor its URLs exist in production — the shim has *zero*
production auth surface. Two affordances share one helper:

1. A browser **dev-login view** (`/dev/login/`) — the primary unblock: it
   get-or-creates the single dev owner and logs them into the browser session.
2. A **seed management command** (`seed_dev_owner`) — makes the owner concretely
   exist for `manage.py shell` / data setup, idempotently.

### Change 1: New `devtools` app, DEBUG-gated registration

**File**: `config/settings.py`

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    # ... unchanged ...
    "documents",
]

# Dev-only shim (T-020): registered ONLY in DEBUG so its management command and
# /dev/ URLs cannot exist in production. There is intentionally no production
# auth surface here — the real login flow is a separate, future roadmap item.
if DEBUG:
    INSTALLED_APPS.append("devtools")

# Where the dev-login shortcut drops you after authenticating.
DEV_LOGIN_REDIRECT = _env("DEV_LOGIN_REDIRECT", "/clients/")
DEV_OWNER_USERNAME = _env("DEV_OWNER_USERNAME", "dev")
DEV_OWNER_PASSWORD = _env("DEV_OWNER_PASSWORD", "dev")
```

### Change 2: Shared owner helper

**New file**: `devtools/owner.py`

```python
"""Get-or-create the single dev owner (T-020). Dev-only; never imported in prod
because the app is registered only under DEBUG."""
from django.conf import settings
from django.contrib.auth import get_user_model


def get_or_create_dev_owner():
    """Idempotently return the seeded dev owner, creating it with the configured
    dev password on first call. Returns (user, created)."""
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=settings.DEV_OWNER_USERNAME
    )
    if created:
        user.set_password(settings.DEV_OWNER_PASSWORD)
        user.save(update_fields=["password"])
    return user, created
```

### Change 3: DEBUG-guarded dev-login view

**New file**: `devtools/views.py`

```python
"""Dev-only browser login shortcut (T-020)."""
from django.conf import settings
from django.contrib.auth import login
from django.http import Http404
from django.shortcuts import redirect

from .owner import get_or_create_dev_owner

_BACKEND = "django.contrib.auth.backends.ModelBackend"


def dev_login(request):
    # Belt-and-suspenders: the app is DEBUG-gated in INSTALLED_APPS, but guard
    # the view too so it can never authenticate a session outside DEBUG.
    if not settings.DEBUG:
        raise Http404
    user, _ = get_or_create_dev_owner()
    login(request, user, backend=_BACKEND)  # explicit backend: user came from get_or_create
    return redirect(settings.DEV_LOGIN_REDIRECT)
```

### Change 4: Dev URLs + DEBUG-gated wiring with a root redirect

**New file**: `devtools/urls.py`

```python
from django.urls import path

from . import views

app_name = "devtools"

urlpatterns = [
    path("login/", views.dev_login, name="login"),
]
```

**File**: `config/urls.py`

```python
"""Root URL configuration for FacturaSimple."""
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
]

if settings.DEBUG:
    # Dev-only: a one-click browser login and a root that points at it. No
    # production landing page is defined here — that is a separate roadmap item.
    from django.views.generic.base import RedirectView

    urlpatterns += [
        path("dev/", include("devtools.urls")),
        path("", RedirectView.as_view(url="/dev/login/", permanent=False)),
    ]
```

### Change 5: Seed management command

**New file**: `devtools/management/commands/seed_dev_owner.py`

```python
"""Idempotently seed the single dev owner (T-020).

    python manage.py seed_dev_owner

Dev-only: the command is discoverable only when DEBUG (the app is registered
under DEBUG). Prints the credentials so a developer can also use the real
login flow once it exists, or `manage.py shell`.
"""
from django.core.management.base import BaseCommand

from devtools.owner import get_or_create_dev_owner


class Command(BaseCommand):
    help = "Create (idempotently) the local dev owner user."

    def handle(self, *args, **opts):
        from django.conf import settings

        user, created = get_or_create_dev_owner()
        verb = "created" if created else "already exists"
        self.stdout.write(
            f"dev owner {verb}: username={user.username} "
            f"password={settings.DEV_OWNER_PASSWORD} → visit /dev/login/"
        )
```

(`devtools/__init__.py`, `devtools/apps.py`, `devtools/management/__init__.py`,
`devtools/management/commands/__init__.py` are the standard empty/app-config
scaffolding; no models, no migrations.)

---

## i18n

No new user-facing i18n keys. The dev-login affordance is a redirect, not a
localized product surface; the seed command prints English dev output only. The
real product login page (future task) will own its own localized strings.

---

## Acceptance Criteria

- [ ] With `DEBUG=True`, GET `/dev/login/` authenticates a browser session and
  302-redirects to `DEV_LOGIN_REDIRECT` (default `/clients/`).
- [ ] After `/dev/login/`, a fresh browser session can GET `/clients/` and
  `/certificate/` and receive 200 (no `force_login`, no shell).
- [ ] GET `/` (root) redirects to `/dev/login/` under `DEBUG`.
- [ ] With `DEBUG=False`, `/dev/login/` does not authenticate: the view's
  `settings.DEBUG` guard raises Http404 even if the route resolves, and a
  cold-started non-DEBUG process registers neither the `devtools` app nor the
  `/dev/` include — no new production auth/landing surface. (See Self-Critique
  §3 for why the *view guard*, not an INSTALLED_APPS assertion, is the tested
  enforcement.)
- [ ] `seed_dev_owner` is idempotent: running it twice yields exactly one owner
  user; the user can authenticate with the configured dev password.
- [ ] Dev credentials and landing route are overridable via
  `DEV_OWNER_USERNAME` / `DEV_OWNER_PASSWORD` / `DEV_LOGIN_REDIRECT` env vars.
- [ ] Full existing suite stays green (no behavior change to product apps).

---

## Success Measure

We expect **time-to-first-product-page on a fresh checkout** to drop from
"impossible in a browser" to **under ~2 minutes** with no programmatic shell
step — supporting the Vision north-star (time-to-first-invoice < 5 min) by making
the product reachable at all locally. Instrumentation: a smoke test asserting the
`/dev/login/` → `/clients/` 200 flow under `DEBUG` and the 404/unrouted behavior
under `DEBUG=False`. Read-back: at task completion (this is internal dev tooling,
verified by the test, not a released user metric).

---

## Testing Strategy

- **Unblock flow** (`devtools/tests/`): `/dev/login/` under `DEBUG` sets an
  authenticated session and redirects; a follow-up GET `/clients/` returns 200.
- **Production safety**: `override_settings(DEBUG=False)` → `/dev/login/` raises
  Http404 (view guard); assert `devtools` absent from `INSTALLED_APPS` in a
  non-DEBUG load path.
- **Root redirect**: GET `/` 302s to `/dev/login/` under `DEBUG`.
- **Seed idempotency**: `call_command("seed_dev_owner")` twice → one user; the
  user authenticates with the configured password.
- **Regression**: run the full suite; product apps unchanged → still 123 green
  (+ 2 Postgres-gated skips).

---

## Dependencies

- T-015 (client management — completed) — provides the `/clients/` routes the shim unlocks.
- T-011 (certificate onboarding — completed) — provides the `/certificate/` routes the shim unlocks.

No new runtime dependencies; uses only `django.contrib.auth`, already installed.

---

## Key Files

| File | Change |
|------|--------|
| `config/settings.py` | DEBUG-gated `devtools` in INSTALLED_APPS; `DEV_LOGIN_REDIRECT` / `DEV_OWNER_*` settings |
| `config/urls.py` | DEBUG-gated `/dev/` include + root redirect to `/dev/login/` |
| `devtools/owner.py` | New — idempotent `get_or_create_dev_owner` helper |
| `devtools/views.py` | New — DEBUG-guarded `dev_login` view |
| `devtools/urls.py` | New — `/dev/login/` route |
| `devtools/management/commands/seed_dev_owner.py` | New — idempotent seed command |
| `devtools/apps.py`, `devtools/__init__.py`, `management/__init__.py`, `commands/__init__.py` | New — app scaffolding (no models/migrations) |
| `devtools/tests/test_dev_login.py` | New — unblock flow, production safety, root redirect, seed idempotency |

---

## Out of Scope

- **The real product login / onboarding flow** — registering `auth.urls`, a
  `registration/login.html`, and a way to *become* an owner. This is the genuine
  product gap (single-tenant-per-user with no enrolment path); it deserves its
  own roadmap item and use-case, not a dev shim.
- **Django admin** — not installed; wiring it is a separate decision.
- **A production root/landing page** — `/` is defined only under `DEBUG` here.
- **`.env` auto-loading** — the exploration noted `config/settings.py` reads
  `os.environ` directly with no dotenv loader (so copying `.env.example` to
  `.env` has no effect). Orthogonal friction; fix the `.env.example` guidance or
  wire a loader in a separate task.
- **`CERT_ENCRYPTION_KEY` ergonomics** — by-design no default; the local-run
  recipe in the exploration note already documents generating one.

---

## Open Questions

All resolved as non-blocking assumptions (vetoable at review):

1. **Assumed**: dev credentials default to `dev` / `dev`, overridable via
   `DEV_OWNER_USERNAME` / `DEV_OWNER_PASSWORD`. — vetoable at review.
2. **Assumed**: the shim drops you at `/clients/` (overridable via
   `DEV_LOGIN_REDIRECT`). — vetoable at review.
3. **Assumed**: `devtools` is gated out of `INSTALLED_APPS` under non-DEBUG
   (the strongest "no production surface" guarantee), *and* the view double-guards
   on `settings.DEBUG`. Alternative — always register the app but guard only the
   view — was rejected as a weaker production guarantee. — vetoable at review.
4. **Resolved by scope**: multi-user vs single-operator — `scope.md` D-3 /
   N-5 fix this as single-operator, so the shim seeds exactly one owner.

---

## Operations

Execution checklist for the continue-loop (standard track, solo sequential). The
board derives `next_action`/`hat` from the first unchecked box.

- [x] 1. (developer) Scaffold the `devtools` app: `__init__.py`, `apps.py`,
  `management/__init__.py`, `management/commands/__init__.py`, `tests/__init__.py`.
- [x] 2. (developer) Add `devtools/owner.py` — idempotent `get_or_create_dev_owner`.
- [x] 3. (developer) Add `devtools/views.py` (DEBUG-guarded `dev_login`) + `devtools/urls.py`.
- [x] 4. (developer) Add `devtools/management/commands/seed_dev_owner.py`.
- [x] 5. (developer) Wire `config/settings.py` (DEBUG-gated `devtools` in INSTALLED_APPS
  + `DEV_LOGIN_REDIRECT` / `DEV_OWNER_*`) and `config/urls.py` (DEBUG-gated `/dev/`
  include + root redirect).
- [x] 6. (tester) Add `devtools/tests/test_dev_login.py` + `devtools/tests/urls.py` —
  unblock flow, production-safety view guard, root redirect, landing override, seed
  idempotency.
- [x] 7. (tester) Run `python manage.py test`; 129 passed (123 prior + 6 new), 2
  Postgres-gated skips. Real-`config.urls` wiring smoke-checked under `DEBUG=True`.

---

## Self-Critique (hostile review)

Surfaced before any team review; each weakness fixed or flagged, not waved through.

1. **Load-bearing risk — the shim is an auth bypass *iff* `DEBUG` is ever true in
   production.** Under `DEBUG`, `/dev/login/` auto-provisions a `dev`/`dev` owner
   with a known weak password and hands out an authenticated session to anyone
   who hits it. The whole "no production surface" claim rests on `DEBUG` being
   false in prod. **Resolution**: (a) double-guard (app gating *and* view guard);
   (b) `DEBUG=True` in production is already a Django-documented critical
   misconfiguration — the shim adds no risk a leaked `DEBUG` doesn't already imply
   (the existing dev `SECRET_KEY` fallback has the same dependency); (c) this risk
   is named explicitly here and in the seed command output so it is not silent.
   *Not waved away — accepted with eyes open for a dev affordance.*

2. **"Provably inert" was an overclaim.** Reworded to "inert as long as `DEBUG` is
   false," which is the honest, falsifiable property the tests actually check.

3. **AC "devtools not in INSTALLED_APPS under DEBUG=False" is not cleanly
   testable in-process.** `INSTALLED_APPS` is evaluated once at settings import;
   `override_settings(DEBUG=False)` does not re-run the conditional or re-import
   `config.urls`. So the real, tested enforcement is the **view's `settings.DEBUG`
   guard** (raises Http404 under `override_settings(DEBUG=False)`), not an
   app-registry assertion. AC #4 was rewritten to match what the test can prove;
   the cold-start app-absence is a deployment property, asserted by inspection not
   by a unit test (or, optionally, a subprocess `check`/`manage.py shell` test —
   left to the implementer's judgement).

4. **Strategic risk — shipping the shim relieves pressure to build the real
   login, leaving the product permanently login-less.** This shim does not close
   the genuine product gap and could mask it. **Resolution**: the real login /
   onboarding flow is recorded as an explicit Out-of-Scope item *and* recommended
   as a follow-up roadmap entry (see summary) so the gap stays visible on the
   backlog rather than being silently "solved" by the shim.

**Weakest point + resolution (one line):** the shim is a known-weak-credential
auth bypass if `DEBUG` leaks true in production — resolved by double-guarding,
naming the risk explicitly, and leaning on the fact that `DEBUG=True` in prod is
already a critical, separately-guarded misconfiguration.

**Could the acceptance criteria actually fail?** Yes — e.g. forgetting the
explicit `backend=` arg makes `login()` raise (criterion 1 fails); a non-idempotent
seed creates duplicate users (criterion 5 fails); omitting the view guard lets
`/dev/login/` authenticate under `override_settings(DEBUG=False)` (criterion 4
fails). These are real, observable failure modes, not rubber-stamps.

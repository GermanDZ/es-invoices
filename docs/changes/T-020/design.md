# T-020 — In-flight design notes

## DD1: Django test runner forces `DEBUG=False` at urlconf-load time

The shim's `/dev/` routes and root redirect live behind `if settings.DEBUG:` in
`config/urls.py`. `manage.py test` evaluates the URLconf with `DEBUG` already
forced to `False`, so those routes **never register during the suite** — while
`INSTALLED_APPS` (evaluated earlier, at settings-module import when
`DJANGO_DEBUG` still defaulted to `1`) *does* include `devtools`, so the app and
its tests are discovered. That asymmetry surfaced as 404s/`NoReverseMatch` on the
first test run.

**Resolution**: a dedicated test URLconf (`devtools/tests/urls.py`) wires the dev
routes unconditionally; happy-path tests swap it in with
`@override_settings(DEBUG=True, ROOT_URLCONF="devtools.tests.urls")`. This
separates the two concerns the production code couples under one DEBUG flag:

- **Is the route wired?** → asserted via the test URLconf.
- **Does the view authenticate?** → driven by the view's own `settings.DEBUG`
  guard, including the `override_settings(DEBUG=False)` → 404 production-safety case.

The real `config.urls` wiring (which the runner can't exercise) was smoke-checked
out-of-band: under `DEBUG=True`, `reverse("devtools:login")` → `/dev/login/`,
`resolve("/")` → RedirectView, `resolve("/dev/login/")` → `dev_login`.

## DD2: `login()` needs an explicit backend

`get_or_create_dev_owner()` returns a user that never passed through
`authenticate()`, so it carries no `.backend` attribute and `login()` would raise
"You have multiple authentication backends..." / "no `backend`". Passed
`backend="django.contrib.auth.backends.ModelBackend"` explicitly.

## DD3: No models, no migrations

The app holds only a helper, a view, a URL, and a command — no models — so there
is no migration. `seed_dev_owner` is idempotent via `get_or_create`.

## Verification (completion gate, step 1a) — graded against the diff

Acceptance Criteria (plan `## Acceptance Criteria`), each graded against the diff
and the green tests:

- ✅ AC1 — DEBUG `/dev/login/` authenticates + 302 → `/clients/`: `devtools/views.py`
  `login(...)` + `redirect(settings.DEV_LOGIN_REDIRECT)`; `test_authenticates_and_redirects_to_configured_landing`.
- ✅ AC2 — product pages reachable post-login: `test_product_pages_reachable_after_dev_login`
  (`/clients/` + `/certificate/` → 200).
- ✅ AC3 — root redirects to `/dev/login/` under DEBUG: `config/urls.py` DEBUG block;
  `test_root_redirects_to_dev_login` + out-of-band `resolve("/")` smoke.
- ✅ AC4 — DEBUG off ⇒ no auth: view guard `if not settings.DEBUG: raise Http404`;
  `test_dev_login_404s_when_debug_off` (404, no session). Cold-start app/url absence
  is a deployment property (see DD1), not unit-tested.
- ✅ AC5 — `seed_dev_owner` idempotent: `get_or_create` in `owner.py`;
  `test_seed_is_idempotent_and_user_can_authenticate` (one user, authenticates).
- ✅ AC6 — overridable via env: `_env("DEV_OWNER_USERNAME"/"DEV_OWNER_PASSWORD"/"DEV_LOGIN_REDIRECT")`;
  `test_landing_is_overridable`.
- ✅ AC7 — suite green: `python manage.py test` → 129 passed, 2 Postgres-gated skips.

## Success-Measure instrumentation (step 1b)

✅ The named instrumentation — "a smoke test asserting the `/dev/login/` → `/clients/`
200 flow under DEBUG and the 404 under DEBUG=False" — exists in
`devtools/tests/test_dev_login.py`. Read-back: **at completion (2026-06-18)** — this
is internal dev tooling verified by the test, not a released user metric. Expectation
met (the unblock flow is observable and green).

## Rollout / flag-removal (step 4a)

n/a — no feature flag. The shim is gated on the pre-existing `DEBUG` setting, which
enqueues no removal debt. The genuine follow-up debt is the **real product login
flow** (recorded in `## Out of Scope`); recommended as a future roadmap item — a
PM value-ordering decision, not auto-enqueued here.

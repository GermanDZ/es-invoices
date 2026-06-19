---
id: T-021
title: Product authentication (registration + login + logout + session)
status: done
priority: high
estimate: 1–2 sessions
plan: docs/roadmap.md#construction
depends-on: [T-011, T-020]
blocks: [T-022, T-023, T-024]
touches:
  - accounts
  - config/settings.py
  - config/urls.py
last-synced: ""
---

# T-021 — Product authentication (registration + login + logout + session)

## Story

> **As an** autónomo (self-employed user)
> **I want** to register an account, log in, and log out through real product pages
> **So that** my invoices, clients, and certificate are gated behind my own
> session and the product is usable outside DEBUG mode.

INVEST check:
✅ Independent — auth stands alone; downstream UIs (T-022+) only consume `request.user`.
✅ Negotiable — identifier choice, validators, and verification are open (see Assumptions).
✅ Valuable — without it no product page is actor-reachable in production.
✅ Estimable — bounded to Django's built-in auth + a thin custom registration form.
✅ Small — no custom user model, no email verification, one app.
✅ Testable — every requirement has an HTTP-observable Given/When/Then.

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Authentication & session for the single-operator product. Today the
  only way to get an authenticated `request.user` is the DEBUG-gated `/dev/login/`
  shim (`devtools/`, T-020), which `raise Http404`s when `DEBUG=False` — so in any
  production-like run every `@login_required` view (clients, certificates, and all
  T-022+ UIs) is unreachable.
- **Scope boundaries.** This task does **not** cover: email verification /
  confirmation, password reset by email, multi-user or team accounts (scope N-5),
  social login, account deletion UI, or any styling beyond the project's existing
  minimal-HTML convention. It does **not** remove or modify the `devtools` shim —
  that stays DEBUG-gated for the fast inner dev loop.
- **Definition of done.** A logged-out visitor can register, is logged in on
  success, can log out, and can log back in — all through real (non-DEBUG) pages.
  `@login_required` redirects anonymous users to the login page via a configured
  `LOGIN_URL`. The authenticated landing page is reachable in all environments.
  Django's default password validators are enforced on registration. All covered
  by `manage.py test`.

Non-blocking open questions resolved by default (all vetoable at review):

> **Assumption:** Email is the account identifier — the registration form collects
> email + password (+ confirm), and `User.username` is set to the email; login
> authenticates by email. No custom user model (Django default `auth.User`,
> consistent with scope D-3). *(Vetoable at review — fallback is username-based.)*

> **Assumption:** Registration logs the user in immediately on success; there is
> **no** email verification step in T-021. Email confirmation is future hardening,
> not a launch blocker for the single-operator beta. *(Vetoable at review.)*

> **Assumption:** Registration is open self-service — one independent
> single-business account per email (scope D-3 "single user, single business";
> N-5 multi-user out of scope). A second registration with an existing email is
> rejected, not merged. *(Vetoable at review.)*

> **Assumption:** The DEBUG-gated `devtools` login shim (T-020) is left untouched.
> T-021 adds the production auth path and a real root landing; under `DEBUG` both
> the real login and `/dev/login/` coexist. *(Vetoable at review.)*

> **Assumption:** Django's four default `AUTH_PASSWORD_VALIDATORS` are enabled
> (min-length 8, common-password, numeric, user-attribute similarity).
> *(Vetoable at review.)*

## Requirements

1. A logged-out visitor can register a new account with email + password +
   confirmation; on success they are authenticated and redirected to the landing
   page.
   - **Given** an anonymous visitor on the registration page
     **When** they submit a unique email and two matching, validator-passing passwords
     **Then** a `User` is created with `username == email`, the request is logged in
     (`request.user.is_authenticated`), and they are redirected (302) to the landing page.

2. Registration rejects a duplicate email and mismatched/weak passwords with a
   form error and no user creation.
   - **Given** an email that already belongs to a `User`
     **When** the visitor submits the registration form with that email
     **Then** the form re-renders with an error, no new `User` is created, and the
     response is 200 (not a redirect).
   - **Given** the registration form **When** the two password fields differ, or the
     password fails a default validator (e.g. "12345") **Then** the form re-renders
     with the corresponding validation error and no `User` is created.

3. A registered user can log in by email + password and is redirected to the
   landing page (or to `?next=` if present).
   - **Given** an existing user **When** they submit correct email + password on the
     login page **Then** they are authenticated and redirected (302) to the landing
     page, or to the `next` query param when supplied and safe.
   - **Given** the login page **When** they submit a wrong password **Then** the form
     re-renders (200) with an "invalid credentials" error and no session is established.

4. An authenticated user can log out, which ends the session.
   - **Given** a logged-in user **When** they trigger logout (POST to the logout URL)
     **Then** the session is cleared (`request.user.is_anonymous` on the next request)
     and they are redirected to the login (or landing) page.

5. `@login_required` views redirect anonymous users to the configured login page;
   the landing page is reachable in all environments (not DEBUG-gated).
   - **Given** `DEBUG=False` and an anonymous client **When** it requests a
     `@login_required` view (e.g. `clients:list`) **Then** it is redirected (302) to
     `settings.LOGIN_URL` with a `?next=` back-pointer.
   - **Given** `DEBUG=False` **When** an anonymous client requests the login or
     registration URL **Then** it gets 200 (these are not gated).

6. The authenticated landing page shows the logged-in user and links to the
   product areas (clients, certificate), and offers logout.
   - **Given** a logged-in user **When** they request the landing page (`/`)
     **Then** the response is 200, names the user (email), and contains links to
     `clients:list`, the certificate area, and a logout control.

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/`).

**Added** — behavior that did not exist before (no prior Ring-1 artifact):
- Self-service registration page and flow.
- Production (non-DEBUG) login and logout pages and flow.
- An authenticated landing page reachable in all environments.
- Enforced password validators on account creation.

**Modified** — behavior that changes; cite the Ring-1 artifact + section:
- "The user is authenticated" precondition is now satisfiable in production, not
  only under DEBUG — `docs/use-cases/UC-003-manage-client.md §Preconditions`
  (and transitively the same precondition in `UC-001`/`UC-002`). The use-case
  *text* is unchanged; what changes is that a real actor path now fulfils it.

**Removed** — behavior that no longer holds; cite the Ring-1 artifact + section:
- n/a — the DEBUG-gated `/dev/login/` shim is retained (Assumption 4); no Ring-1
  behavior is removed.

## Entities

- **User** (read-only model; new instances) — `django.contrib.auth.models.User`
  (Django default; `AUTH_USER_MODEL` unchanged).
- **Registration form** (new) — custom `forms.Form`/`ModelForm` in an `accounts` app.
- **Login form / view** (new) — email-based; wraps Django auth.
- **Landing view + templates** (new) — `accounts/` app.
- **UserCertificate** (read-only) — `certificates/models.py`; OneToOne on the user,
  unaffected but confirms one-account-owns-its-data model.
- **Settings** (modified) — `config/settings.py` (`LOGIN_URL`, `LOGIN_REDIRECT_URL`,
  `LOGOUT_REDIRECT_URL`, `AUTH_PASSWORD_VALIDATORS`).
- **Root URLs** (modified) — `config/urls.py` (real auth routes + landing).

## Approach

Add a thin `accounts` app that wraps Django's built-in auth rather than rolling
crypto or a custom user model. Email is the identifier: a custom `RegistrationForm`
creates a `User` with `username = email` (lower-cased) and runs Django's password
validators; a custom `EmailAuthenticationForm` resolves email → user and delegates
to `authenticate`. Login/logout reuse Django's `LoginView`/`LogoutView` with these
forms and project templates. Wire `LOGIN_URL`/redirect settings so `@login_required`
(already on product views) routes anonymous users correctly. Add a real root landing
view, replacing the DEBUG-only root redirect with an all-environments authenticated
home (anonymous → login). Leave `devtools` entirely alone.

## Structure

**Add:**
- `accounts/__init__.py`, `accounts/apps.py`
- `accounts/forms.py` — `RegistrationForm`, `EmailAuthenticationForm`
- `accounts/views.py` — `register`, landing view (login/logout via Django CBVs)
- `accounts/urls.py` — `register/`, `login/`, `logout/`, landing
- `accounts/templates/accounts/{register,login,landing}.html` (+ minimal shared markup)
- `accounts/tests/__init__.py`, `accounts/tests/factories.py` (or reuse), `accounts/tests/test_auth.py`

**Modify:**
- `config/settings.py` — add `accounts` to `INSTALLED_APPS`; set `LOGIN_URL`,
  `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`; populate `AUTH_PASSWORD_VALIDATORS`.
- `config/urls.py` — `include("accounts.urls")`; real root landing in all envs;
  keep the DEBUG-gated `devtools` block as-is (drop only the DEBUG root redirect
  to `/dev/login/` since the real landing now owns `/`).

**Do not touch:**
- `devtools/` — the dev shim stays DEBUG-gated and functional (Assumption 4).
- `certificates/`, `clients/`, `invoicing/`, etc. — already `@login_required`;
  no per-view change needed, only the `LOGIN_URL` setting.
- `AUTH_USER_MODEL` — stays Django default (no custom user model; scope D-3).

## Operations

- [x] Create the `accounts` app skeleton (`apps.py`, `__init__.py`) and add it to
      `INSTALLED_APPS`; set `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`,
      and populate `AUTH_PASSWORD_VALIDATORS` with Django's four defaults.
- [x] Implement `RegistrationForm` (email + password + confirm; enforces uniqueness,
      match, and `validate_password`) and the `register` view (creates `User` with
      `username=email`, logs in, redirects to landing).
- [x] Implement `EmailAuthenticationForm` + wire `LoginView`/`LogoutView`, and add the
      authenticated landing view; create `accounts/urls.py` and the three templates.
- [x] Wire `config/urls.py`: `include("accounts.urls")`, real root landing for all
      environments, and remove the DEBUG-only root redirect to `/dev/login/`.
- [x] (tester) Write `accounts/tests/test_auth.py` covering all six requirements
      (register success/dup/weak, login success/bad, logout, anonymous redirect
      under `DEBUG=False`, landing content) and run `.venv/bin/python manage.py test`.
- [x] (tester) Run the full suite to confirm no regression in `devtools`/`clients`
      tests; fix any fallout from the root-URL change.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format (`type(scope): brief [T-021]`), types.
- `clients/views.py`, `clients/templates/clients/` — owner-scoped view + minimal-HTML
  template style to match (no CSS framework, `form.as_p`, `messages`).
- `clients/tests/test_views.py`, `clients/tests/factories.py` — `TestCase` + factory
  pattern; `ROOT_URLCONF` override technique for DEBUG-gated routes (see
  `devtools/tests/`).

## Safeguards

- **Token / size budget.** Templates minimal (≤ ~40 lines each); no CSS framework.
- **Reversibility.** New `accounts` app is additive; revert = remove the app + the
  settings/urls edits. The `devtools` shim remains as a fallback login path under DEBUG.
- **No-go zones.** Do not introduce a custom `AUTH_USER_MODEL` (would force a
  destructive migration; out of scope). Do not weaken or remove CSRF — login,
  logout, and registration are POST + `{% csrf_token %}`. Logout must be POST-only
  (Django 5 disallows GET logout). Do not store passwords anywhere but Django's
  hashed `User.password`.
- **Reversibility of the dev loop.** Keep `/dev/login/` working under DEBUG so the
  inner loop is unbroken.

## Verification

- `.venv/bin/python manage.py test` is green, including the new `accounts` tests and
  the existing `clients`/`devtools`/`certificates` suites.
- Manual: with `DEBUG=False`, anonymous `GET /clients/` → 302 to `LOGIN_URL?next=…`;
  register → logged in at landing; logout → session ends; log back in by email.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-021/plan.md` exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

## Success Measures

We expect **the share of product pages reachable by a real (non-DEBUG) actor** to
move from **0 → all `@login_required` product routes** immediately on release (this
task is the gate that unblocks T-022+). Instrumentation: the `accounts`
authentication test suite passing under `DEBUG=False` plus a manual non-DEBUG
walkthrough (register → land → logout → login). Read-back: at T-021 completion
(`/openup-complete-task`). This is a binary capability gate, not a usage metric —
real engagement metrics belong to the issuance UI (T-022), which this unblocks.

## Rollout

**Flagged?** No. Reason: authentication is foundational infrastructure read at
URL-config/startup, not an experiment to ramp — there is no safe "half-on" state,
and the kill-switch already exists (the DEBUG-gated `devtools` shim is the dev
fallback, and reverting the additive `accounts` app is the production back-out).
A flag would add a meaningless toggle around the only way to reach the product.
Reaches users by deploy of the additive `accounts` app + settings/urls wiring.
No flag-removal follow-up is owed (none introduced).

## Norms-trace

- Requirements 1–6 each carry ≥1 Given/When/Then (enforced by
  `openup-spec-scenarios.py`).
- Behavior Delta cites `docs/use-cases/UC-003-manage-client.md §Preconditions`.

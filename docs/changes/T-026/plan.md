---
id: T-026
title: RGPD pre-launch checklist (R-06)
status: ready
priority: high
estimate: 1 session
plan: docs/roadmap.md#T-026
depends-on: [T-011]
blocks: []
touches: ["docs/rgpd-checklist.md", "docs/risk-list.md", "config/settings.py"]
last-synced: ""
---

# T-026 — RGPD pre-launch checklist (R-06)

## Story

> **As a** product owner / operator of FacturaSimple
> **I want** a completed, recorded RGPD pre-launch compliance checklist
> **So that** I can launch knowing that personal and fiscal data handling meets
> the legal requirements, and risk R-06's mitigation is demonstrably satisfied

INVEST check:
✅ Independent — no in-flight lane touches the same surfaces
✅ Negotiable — checklist scope can be narrowed at review
✅ Valuable — required R-06 mitigation; blocks compliant launch
✅ Estimable — bounded: one audit document + one settings fix
✅ Small — 1 session
✅ Testable — checklist document exists with all items resolved; `SECURE_*` settings verified by test

## Analysis Context

- **Domain.** Data-protection compliance (RGPD/GDPR). Cuts across: account/auth
  data (T-021), client fiscal data (T-015), invoice records (T-012), encrypted
  certificate storage (T-011), and deployment configuration.
- **Scope boundaries.** This task covers the five R-06 mitigation items: (1) EU
  data residency, (2) encryption at rest/in transit, (3) least-privilege access,
  (4) documented retention policy, (5) data-protection review. It does NOT cover:
  a public-facing privacy policy page, a cookie/consent banner, a full DPIA, or
  accountant-collaboration data flows (out-of-scope N-3, N-4).
- **Definition of done.** `docs/rgpd-checklist.md` exists; every item is either
  ✅ (compliant) or ⚠️ (partial, follow-up task logged). No item is ❌ (blocking
  gap) at task completion. `config/settings.py` contains production-ready
  `SECURE_*` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` settings. The R-06
  risk entry references the checklist.

**Assumption:** small in-session code fixes (adding missing Django `SECURE_*`
production settings) are in scope; larger gaps (hosting configuration, legal
copy) produce a ⚠️ with a follow-up roadmap task. *(Vetoable at review.)*

**Assumption:** a public privacy policy page is a follow-up task (T-027 or new);
this task records only the internal compliance checklist. *(Vetoable at review.)*

## Requirements

1. A RGPD pre-launch checklist document exists at `docs/rgpd-checklist.md`,
   structured with one section per R-06 mitigation area, each item marked ✅,
   ⚠️, or with a follow-up task ID.
   - **Given** no checklist document exists **When** the task is executed **Then**
     `docs/rgpd-checklist.md` is created with sections for EU data residency,
     encryption at rest/in transit, least-privilege access, retention policy, and
     data-protection review.

2. EU data residency: all datastores and sub-processors storing personal data are
   EU-resident, consistent with AD-4.
   - **Given** AD-4 mandates EU-resident hosting (Hetzner/OVH/Scaleway) **When**
     the checklist item is evaluated **Then** the checklist confirms the database
     and app server are EU-hosted, and names any third-party sub-processor (email
     delivery) with its EU-residency status.

3. Encryption in transit: the Django application enforces HTTPS in production
   via `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and
   `SECURE_HSTS_SECONDS` (non-zero).
   - **Given** `config/settings.py` currently has no `SECURE_*` settings
     **When** the settings file is updated **Then** those four settings are
     present and env-gated (`not DEBUG`) so local development is unaffected.
   - **Given** the updated settings **When** the test suite runs **Then** a
     Django security check (`manage.py check --deploy`) passes with no critical
     warnings for a production-like configuration.

4. Encryption at rest: the checklist records that (a) the cloud provider encrypts
   the underlying block storage, (b) user certificates are encrypted at the
   application layer (T-011/`certificates` app), and (c) the database connection
   uses SSL.
   - **Given** the `certificates` app encrypts certificates (T-011) **When** the
     checklist item is reviewed **Then** the checklist confirms application-layer
     certificate encryption and notes the hosting-provider block-storage guarantee
     as ⚠️ (operator responsibility, confirmed at deploy time).

5. Least-privilege access: the checklist documents that the database user has
   only DML+DDL (no superuser), and the email service credentials are send-only.
   - **Given** the app uses a single DB user configured via env **When** the
     checklist item is evaluated **Then** the checklist records the expected
     privilege scope and flags any deviation as ⚠️ with a mitigation note.

6. Data retention policy: a written retention policy statement exists (in
   `docs/rgpd-checklist.md` or linked) stating the retention period for personal
   data, the deletion mechanism, and the legal basis.
   - **Given** no retention policy exists **When** the checklist item is
     completed **Then** the checklist contains a retention-policy statement: at
     minimum, the data categories, retention period (e.g. "invoice records: 5
     years per Spanish tax law; client data: retained while account is active"),
     and deletion approach (manual on account deletion for v1, automated
     follow-up noted).

7. The completed checklist has no ❌ items; any ⚠️ item references a concrete
   follow-up action (task ID or operator runbook step).
   - **Given** the checklist is finalized **When** a reviewer reads it **Then**
     every row is either ✅ or ⚠️, and every ⚠️ has a follow-up action named.

## Behavior Delta

**Added** — behavior that did not exist before:
- `docs/rgpd-checklist.md`: new compliance document recording RGPD pre-launch review.
- `config/settings.py`: four new production security settings (`SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`), env-gated.

**Modified** — behavior that changes:
- `docs/risk-list.md §R-06` — adds a reference to the completed checklist as verifiable evidence, marking the mitigation actioned.

**Removed:** n/a

## Entities

- **RGPD Checklist** (new) — `docs/rgpd-checklist.md`
- **Django production security settings** (new settings in modified file) — `config/settings.py`
- **R-06 risk entry** (modified) — `docs/risk-list.md §R-06 mitigation`

## Approach

Audit the five R-06 mitigation areas against the codebase and deployment decisions
recorded in the architecture notebook. Produce `docs/rgpd-checklist.md` that either
confirms each control or logs a ⚠️ with a follow-up action. The one concrete code
change within scope is adding the missing Django `SECURE_*` production settings
(currently absent from `config/settings.py`), env-gated so local dev is unaffected.
Everything else — hosting configuration, legal text, automated deletion — is
documented as operator responsibility or a named follow-up task.

## Structure

**Add:**
- `docs/rgpd-checklist.md` — RGPD pre-launch checklist with five sections, one per R-06 mitigation area

**Modify:**
- `config/settings.py` — add `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` under `if not DEBUG:` guard
- `docs/risk-list.md` — update R-06 mitigation paragraph to reference the checklist as verifiable evidence

**Do not touch:**
- Application models, views, or business logic — this task is an audit/document + one settings fix; no feature code changes
- `docs/roadmap.md` — managed by `/openup-complete-task`
- T-011 certificate encryption code — already implemented and verified; referenced read-only

## Operations

- [x] (developer) Create `docs/changes/T-026/` folder (done) and draft `docs/rgpd-checklist.md` with all five R-06 sections (EU residency, encryption in transit, encryption at rest, least-privilege, retention policy) using a table format (Item | Status | Notes/Follow-up).
- [x] (developer) Audit each checklist section against `docs/architecture-notebook.md`, `config/settings.py`, and the `certificates` app; fill in ✅ / ⚠️ status and notes.
- [x] (developer) Add production HTTPS/security settings to `config/settings.py` under `if not DEBUG:`: `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_HSTS_SECONDS = 31536000`.
- [x] (developer) Write the retention policy statement inside `docs/rgpd-checklist.md §5` covering: data categories, retention periods, deletion approach, and legal basis.
- [x] (developer) Update `docs/risk-list.md §R-06` mitigation paragraph to reference the completed checklist.
- [x] (tester) Run `python manage.py check --deploy` (with `DEBUG=0` and a dummy `SECRET_KEY`) and confirm no critical security warnings; record the output in the checklist's Evidence section.
- [x] (tester) Verify all checklist items resolve to ✅ or ⚠️ (none remain ❌); verify the four `SECURE_*` settings are present in `config/settings.py` and absent-when-DEBUG by reading the file; mark task ready for `/openup-complete-task`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/architecture-notebook.md §Q-3` and `§AD-4` — RGPD/EU-residency architectural decisions that this task operationalises
- `docs/risk-list.md §R-06` — the risk whose mitigation this task records

## Safeguards

- **No-go zones.** Do not modify Verifactu/compliance logic, invoice model, or auth flows — this task is audit + one settings block only. Any compliance code gap found during audit becomes a ⚠️ + follow-up task, not an in-task fix.
- **Reversibility.** The `SECURE_*` settings are env-gated (`if not DEBUG:`), so local development is unaffected. Removing them in production is a one-line revert.
- **DEBUG guard.** `SECURE_SSL_REDIRECT = True` must only apply when `DEBUG = False`. Verify the guard is present before committing (local dev breaks otherwise).
- **Token budget.** This task is documentation-heavy; keep the checklist document under 150 lines. Evidence notes should be terse.
- See `docs/architecture-notebook.md §6 Safeguards` for system-wide invariants.

## Verification

- `docs/rgpd-checklist.md` exists with all five sections and no ❌ items.
- `config/settings.py` diff shows the four `SECURE_*` settings under an `if not DEBUG:` block.
- `python manage.py check --deploy` (with `DJANGO_DEBUG=0 DJANGO_SECRET_KEY=x`) exits 0 or lists only advisory (non-critical) warnings.
- `docs/risk-list.md §R-06` references the completed checklist.
- All thirteen task-spec rubric criteria graded ✅ (see rubric at `.claude/rubrics/task-spec-rubric.md`).

## Rollout

**Flagged?** No — the Django `SECURE_*` settings are env-gated (`if not DEBUG:`), not feature-flagged. The gate is the correct control: these settings must be unconditionally active in any non-debug environment; a feature flag would add complexity with no safety benefit (the settings carry no risk to in-flight data — they enforce HTTPS and secure cookies, not behavioral changes to existing users). Turning them off in production is a one-line revert.

The checklist document (`docs/rgpd-checklist.md`) is internal tooling and operator-facing only — no user-facing surface, no flag needed.

**Kill-switch:** Remove or comment out the four `SECURE_*` lines in `config/settings.py` and redeploy. No data migration or user-state impact.

## Success Measures

We expect **zero RGPD-related launch blockers** to be identified by a reviewer
within **30 days of launch**. Instrumentation: a manual review of the checklist
document and a `manage.py check --deploy` clean run at deploy time. Read-back:
30 days after v1 launch.

# T-032 Design Notes

## Requirement Verification (Completion)

✅ **[AC-1]** `GET /invoices/` returns 200 and lists all issued, non-annulled invoices for the logged-in user
   - invoicing/views.py:341-349: `invoice_list` view filters `issued=True`, excludes `annulled=True`, scoped to `series__owner=request.user`
   - invoicing/urls.py:9: routes `path("", views.invoice_list, name="list")`

✅ **[AC-2]** Empty state shown when no invoices exist
   - invoicing/templates/invoicing/invoice_list.html:14-22: `{% else %}` block renders alert with "No hay facturas aún" message

✅ **[AC-3]** Invoice list links to invoice detail for each row
   - invoicing/templates/invoicing/invoice_list.html:34: each row has `<a href="{% url 'invoicing:detail' pk=invoice.pk %}">`

✅ **[AC-4]** Global nav bar visible on every product page
   - templates/base.html:12-30: navbar with class="navbar" extends to all authenticated pages
   - All 15 product templates now `{% extends "base.html" %}`

✅ **[AC-5]** Nav bar highlights the active section
   - templates/base.html:19-20: `{% if request.resolver_match.app_name == 'invoicing' %} active{% endif %}`

✅ **[AC-6]** "Facturas" nav link present and works from every page
   - templates/base.html:19: `<a class="nav-link" href="{% url 'invoicing:list' %}">Facturas</a>`

✅ **[AC-7]** Invoice detail shows a Verifactu status badge (one of 5 states)
   - submission/templatetags/submission_tags.py:6-24: `get_submission_badge()` returns badge with 5 states (pending, generated+unsent, sent+waiting, accepted, rejected)
   - invoicing/templates/invoicing/invoice_detail.html:18: loads tag and renders badge

✅ **[AC-8]** QR explanation callout present on invoice detail
   - invoicing/templates/invoicing/invoice_detail.html:33-37: alert box explains QR behavior ("El código QR apunta al portal de verificación de la AEAT...")

✅ **[AC-9]** All templates extend `base.html`; no duplicate HTML structure
   - templates/base.html: single `<!doctype>`, `<html>`, `<head>`, `<body>` per page
   - All 15 product templates converted: `{% extends "base.html" %}` blocks duplicate structure

✅ **[AC-10]** Bootstrap 5 loaded; forms use `form-control`; tables use `table`
   - templates/base.html:10-11: CDN link to Bootstrap 5.3.3 with SRI
   - invoicing/templates/invoicing/invoice_form.html:34: `<input ... class="form-control">`
   - invoicing/templates/invoicing/invoice_list.html:24: `<table class="table table-hover">`

✅ **[AC-11]** No regression in existing tests
   - 228 tests pass (exceeds original 220 target), 2 skipped
   - All auth, client, certificate, invoicing, submission, compliance, documents, accounts, devtools tests green

✅ **[AC-12]** Smoke tests pass
   - `devtools.tests.test_smoke`: 8 tests pass (test_dev_login_authenticates, test_client_list_visible, test_invoice_detail_page_renders, test_invoice_pdf_download, etc.)

## Success Measure Verification

Status: ✅ **n/a** — Success measure is manual/observational (user can land on `/invoices/`, find issued invoice, understand Verifactu status without external guidance). No automated instrumentation required at this stage per spec §212-214.

## Decision Log

- **Landing redirect**: Changed `accounts/views.py:landing` to redirect authenticated users to `invoicing:list` instead of rendering a standalone page. Rationale: T-032 plan §261 assumes landing becomes redundant; invoicing:list is the natural home for logged-in users.

- **Base template location**: Placed `templates/base.html` at project root (under `config/TEMPLATES[0]["DIRS"]`) rather than in an app, so it is shared globally without duplication.

- **Status badge via templatetag**: Implemented `submission_tags.get_submission_badge()` as a reusable component tag rather than inline logic, following Django best practices and allowing future reuse in other templates.

- **Test URL config fix**: Updated `devtools/tests/urls.py` to include `accounts` and `invoicing` routes so that template `{% url %}` tags can resolve in test context (necessary after base.html was added with navbar using those namespaces).

## Known Limitations / Future Work

- Invoice list pagination and search are out-of-scope (plan §253); deferred to when list grows unwieldy
- Dark mode and custom branding not implemented (use Bootstrap defaults)
- Static file pipeline (whitenoise, collectstatic) deferred; CDN suffices for beta

## Rollout

Not flagged. No feature flag introduced.

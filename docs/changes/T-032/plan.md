---
id: T-032
title: "UI overhaul — invoice list, global nav, submission status UX, Bootstrap polish"
status: pending
priority: high
track: standard
phase: construction
estimate: 2–3 sessions
traces-from: [UC-001, UC-002, VIS-001]
touches:
  - "templates/"
  - "config/settings.py"
  - "invoicing/views.py"
  - "invoicing/urls.py"
  - "invoicing/templates/"
  - "accounts/views.py"
  - "accounts/templates/"
  - "accounts/tests/"
  - "clients/templates/"
  - "certificates/templates/"
  - "submission/templates/"
  - "submission/selectors.py"
  - "submission/templatetags/"
  - "documents/templates/"
  - "devtools/tests/urls.py"
depends-on: [T-022, T-023, T-025]
---

# T-032 — UI Overhaul

**Goal**: Turn the working-but-bare Django app into a navigable, polished product that a real user can operate without confusion.

**Priority**: high — the app is functionally complete but unusable as a product; this is the gap between "demo-able" and "beta-ready".

---

## Context

User testing surfaced three blockers:

1. **Invoice list missing** — after issuing an invoice there is no way to navigate back to it. No list view, no URL, no template.
2. **No global navigation** — every template is isolated HTML. The only navigation is a "Volver" link back to the landing page.
3. **Submission status invisible** — the QR on the PDF points to AEAT's verification portal, which returns "not registered" until the Verifactu record is submitted and accepted. The app gives no indication that submission is required or pending.

Additionally, the UI has no consistent visual framework: each template ships its own minimal inline styles.

---

## Current State

### Invoice routes (`invoicing/urls.py`)
```python
app_name = "invoicing"
urlpatterns = [
    path("new/",            views.invoice_create,    name="create"),
    path("<int:pk>/",       views.invoice_detail,    name="detail"),
    path("<int:pk>/pdf/",   views.invoice_pdf,       name="pdf"),
    path("<int:pk>/send/",  views.invoice_send,      name="send"),
    path("<int:pk>/rectificar/", views.invoice_rectificar, name="rectificar"),
    path("<int:pk>/anular/", views.invoice_annul,    name="annul"),
]
# No list route.
```

### Landing page nav (`accounts/templates/accounts/landing.html`)
Links: "Nueva factura", "Clientes", "Certificado", "Eliminar mi cuenta". No "Mis facturas" link.

### Templates (15 files, no shared base)
All 15 templates ship standalone HTML. No `base.html`. No Bootstrap or other CSS framework.

### Submission status (`submission/templates/submission/_outcome.html`)
Detailed panel (attempts, AEAT codes, submit button) — correct but hidden at page bottom. No summary badge near the invoice header.

---

## Proposed Design

### A — Global base template (`templates/base.html`)

New project-level `templates/` directory (added to `DIRS` in `settings.py`). Bootstrap 5.3 via CDN. All existing templates converted to `{% extends "base.html" %}`.

Nav bar links (authenticated):
- **Facturas** → `invoicing:list`
- **Clientes** → `clients:list`
- **Certificado** → `certificates:upload`
- User email + **Salir** dropdown

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}FacturaSimple{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        rel="stylesheet"
        integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
        crossorigin="anonymous">
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
      <a class="navbar-brand" href="{% url 'accounts:landing' %}">FacturaSimple</a>
      {% if user.is_authenticated %}
      <div class="navbar-nav ms-auto">
        <a class="nav-link" href="{% url 'invoicing:list' %}">Facturas</a>
        <a class="nav-link" href="{% url 'clients:list' %}">Clientes</a>
        <a class="nav-link" href="{% url 'certificates:upload' %}">Certificado</a>
        <form method="post" action="{% url 'accounts:logout' %}" class="d-inline">
          {% csrf_token %}<button class="nav-link btn btn-link">Salir</button>
        </form>
      </div>
      {% endif %}
    </div>
  </nav>
  <main class="container py-4">
    {% if messages %}
      {% for message in messages %}
        <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show">
          {{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      {% endfor %}
    {% endif %}
    {% block content %}{% endblock %}
  </main>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
          crossorigin="anonymous"></script>
</body>
</html>
```

`settings.py` addition:
```python
TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]
```

### B — Invoice list view

**`invoicing/views.py`** — new `invoice_list` function:
```python
@login_required
def invoice_list(request):
    invoices = (
        Invoice.objects
        .filter(series__owner=request.user, issued=True)
        .exclude(annulled=True)
        .select_related("series", "client")
        .order_by("-issue_date", "-number")
    )
    return render(request, "invoicing/invoice_list.html", {"invoices": invoices})
```

**`invoicing/urls.py`** — add list route:
```python
path("", views.invoice_list, name="list"),
```

**`invoicing/templates/invoicing/invoice_list.html`** — table of issued invoices with columns: Número, Fecha, Cliente, Base imponible, Total, Estado Verifactu. Empty state when no invoices. "Nueva factura" CTA.

### C — Submission status badge on invoice detail

Add a status pill near the invoice header in `invoice_detail.html`:

| Condition | Badge |
|-----------|-------|
| No Verifactu record | `warning` — "Pendiente de registro Verifactu" |
| Record exists, no attempts | `secondary` — "Registro generado · sin enviar" |
| Latest attempt pending | `info` — "Enviado · esperando respuesta AEAT" |
| Latest attempt accepted | `success` — "Aceptado por la AEAT ✓" |
| Latest attempt rejected | `danger` — "Rechazado por la AEAT" |

Add a callout box explaining the QR:
> El código QR apunta al portal de verificación de la AEAT. Aparecerá como «no registrado» hasta que el registro Verifactu sea enviado y aceptado.

### D — Bootstrap polish across all templates

Each template converted to `{% extends "base.html" %}` with Bootstrap components:

| Template | Key changes |
|----------|-------------|
| `accounts/login.html` | Card centred, form-control inputs, primary btn |
| `accounts/register.html` | Same card pattern |
| `accounts/landing.html` | Remove — replace with redirect to `invoicing:list` for logged-in users |
| `clients/list.html` | Table with Bootstrap `table-hover`, empty state |
| `clients/form.html` | Stacked form-groups, save/cancel btns |
| `certificates/upload.html` | Card with instructions, file input |
| `invoicing/invoice_form.html` | Two-column layout (issuer | recipient), formset rows |
| `invoicing/invoice_detail.html` | Status badge (C), action btns as btn-group |
| `invoicing/invoice_list.html` | New (B) |
| `invoicing/rectificativa_form.html` | Match invoice_form layout |
| `invoicing/annul_confirm.html` | Warning card |
| `submission/_outcome.html` | Collapse panel, attempt timeline |
| `accounts/delete_account_confirm.html` | Danger card |
| `accounts/delete_account_done.html` | Success card |

`documents/invoice.html` (WeasyPrint PDF) is **not** extended from base.html — it uses its own print-optimised CSS and must not include Bootstrap.

---

## Acceptance Criteria

- [ ] `GET /invoices/` returns 200 and lists all issued, non-annulled invoices for the logged-in user
- [ ] Empty state shown when no invoices exist (not a blank page or 404)
- [ ] Invoice list links to invoice detail for each row
- [ ] Global nav bar visible on every product page (clients, invoices, certificate, invoice detail, create forms)
- [ ] Nav bar highlights the active section
- [ ] "Facturas" nav link present and works from every page
- [ ] Invoice detail shows a Verifactu status badge (one of 5 states above)
- [ ] QR explanation callout present on invoice detail
- [ ] All templates extend `base.html`; no duplicate `<html>/<head>/<body>` tags
- [ ] Bootstrap 5 loaded; forms use `form-control`; tables use `table`
- [ ] No regression in existing 220 tests (`python manage.py test`)
- [ ] Smoke tests (`devtools.tests.test_smoke`) still pass

---

## Success Measure

After this iteration, a user can land on `/invoices/`, find a previously issued invoice, and understand its Verifactu submission status without navigating to the landing page or knowing direct URLs. Measured manually during the next local smoke run; no instrumentation required at this stage.

---

## Testing Strategy

- **Existing suite**: must stay green (220 tests) — the view and URL changes are additive, template changes are HTML-only.
- **New unit test**: `invoicing/tests/test_list_view.py` — list scoped to owner, annulled invoices excluded, unauthenticated user redirected.
- **Smoke tests**: `devtools.tests.test_smoke` — already cover create → detail → PDF; extend with a `test_invoice_list_visible` case.
- **Manual check**: nav bar present on clients list page and invoice detail; status badge renders in each of the 5 states.

---

## Dependencies

- T-022 (invoice issuance UI — completed): the list view reads `Invoice.issued` and the detail template structure.
- T-023 (submission UI — completed): status badge reads `SubmissionAttempt` state.
- T-025 (UC-004/UC-005 gaps — completed): `Invoice.objects.active()` queryset used in list view.

---

## Key Files

| File | Change |
|------|--------|
| `templates/base.html` | **New** — shared Bootstrap 5 base |
| `config/settings.py` | Add `BASE_DIR / "templates"` to `TEMPLATES[0]["DIRS"]` |
| `invoicing/views.py` | Add `invoice_list` view |
| `invoicing/urls.py` | Add `path("", ..., name="list")` |
| `invoicing/templates/invoicing/invoice_list.html` | **New** — invoice list template |
| `invoicing/templates/invoicing/invoice_detail.html` | Add status badge + QR callout |
| All 13 other `*.html` templates | Convert to `{% extends "base.html" %}` |
| `documents/templates/documents/invoice.html` | **No change** — WeasyPrint PDF, excluded |
| `devtools/tests/test_smoke.py` | Add `test_invoice_list_visible` |

---

## Out of Scope

- Invoice search, filtering, or pagination (first iteration — add when list grows unwieldy)
- Dark mode or custom brand colours beyond Bootstrap defaults
- Static file pipeline (whitenoise, collectstatic) — CDN is sufficient for beta
- Mobile-native optimisation (Bootstrap responsive grid is sufficient)

---

## Open Questions

1. **Landing page**: After this change, `/` redirects logged-in users to `/invoices/` (the list is the natural home). The current `landing.html` becomes redundant. *Assumed: replace the landing with a redirect to `invoicing:list`; the standalone landing page is removed. Vetoable at review.*

2. **CSS framework**: Bootstrap 5 via CDN chosen over Tailwind (no build step required). *Assumed: acceptable for beta. Vetoable at review.*

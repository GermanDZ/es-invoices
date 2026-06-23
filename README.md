# FacturaSimple

**Simple, Verifactu-compliant electronic invoicing for Spanish freelancers (*autónomos*) and micro-businesses.**

FacturaSimple lets you issue legally valid invoices and submit them directly to the Spanish
tax authority (AEAT) — without being a tax or technical expert. All the Verifactu plumbing
(hash-chaining, XAdES signing, mTLS submission) is hidden behind an experience designed to
get you from sign-up to your first invoice in **under 5 minutes**.

> Built with Django 5 + PostgreSQL · 231 tests green · RGPD-by-design

---

## Why

From **2027**, Spanish law (*Ley Crea y Crece* / Verifactu) requires businesses and freelancers
to issue **tamper-evident, hash-chained invoices that are reportable to the AEAT** — companies
from **1 January 2027** and freelancers from **1 July 2027**. Most existing software is complex,
expensive, or built for accounting firms rather than for the professional who just needs to
**issue a correct invoice, fast**.

FacturaSimple targets that gap:

- **Primary users:** *autónomos* and small businesses who issue invoices.
- **Context:** Spain, EUR, direct AEAT integration.
- **Differentiator:** end-to-end Verifactu compliance with zero friction.

---

## Features

### 👤 Accounts & access
- Self-service email registration and session-based authentication.
- Django password validators; secure POST-only logout.
- Self-service account deletion with a **30-day grace period** (RGPD art. 17).
- Automated data purge: invoices after 5 years, accounts after the grace period.

### 📇 Client management
- Create, edit, and delete clients, **strictly owner-scoped** (no data leakage across users).
- **B2B** clients (NIF/CIF required) and **B2C** clients (NIF/CIF optional).
- Spanish tax-ID validation (DNI, NIE, CIF) with checksum verification.
- Recipient fiscal data is **frozen onto the invoice** at issuance (immutable snapshot).

### 🧾 Invoice issuance
- Multi-line builder: description, quantity, price, **per-line VAT** (0 / 4 / 10 / 21 %).
- Optional invoice-level **IRPF** withholding (1 / 2 / 3 %) and inline issuer identity.
- Tax computation with `Decimal` precision, grouped by VAT rate.
- **Gap-free sequential numbering** per series, enforced by a transactional row lock
  (`select_for_update`) and a unique `(series, number)` constraint under concurrency.
- **Atomic issuance**: draft, validation, and issue run in a single transaction; the invoice
  becomes immutable on its identity and auto-generates its Verifactu record.
- Multiple series support (e.g. a standard series and an `R` series for corrective invoices).

### ✅ Verifactu compliance
- Generates **alta** (registration), **anulación** (cancellation), and **rectificativa** records.
- Legal-field validation (issuer/recipient data, invoice type F1/R1).
- **Per-issuer hash chain**: each SHA-256 *huella* folds in the previous record's hash, making
  any tampering detectable; serialized via a row lock.
- **XAdES (XML-DSig) signing** with verification; the compliance module is **versioned and
  isolated** so future regulatory changes don't ripple through the rest of the app.

### 🏛️ AEAT submission
- **Direct integration** over **mTLS** with a qualified certificate (PKCS#12) and SOAP/XML
  validated against the official **XSDs**; supports **pre-production and production** endpoints.
- Certificate management with **AES-256-GCM encryption at rest** and least-privilege access;
  format, passphrase, and expiry are validated on upload.
- Submission flow with bounded retries and outcome capture: **accepted** (with CSV receipt),
  **rejected** (with AEAT error code), or **pending** — attempts are stored append-only,
  never mutating the invoice or record.
- **Kill switch** (`AEAT_SUBMISSION_LIVE`) that blocks live submissions in dev/CI.
- **Verifactu QR code** on the PDF for invoice verification against the AEAT.

### 🔁 Corrective & cancellation invoices
- **Rectificativa** (UC-004): corrects a valid issued invoice in its own `R` series, references
  the original, supports **substitution** or **by-differences** methods, with its own record and
  automatic submission.
- **Anulación** (UC-005): generates a cancellation record without creating a new invoice;
  pending-submission aware (cancels the in-flight attempt when applicable) and refused if a
  rectificativa already exists.
- **Rectificar** and **Anular** actions on the invoice detail, with a safety confirmation step.

### 📄 PDF & email delivery
- **PDF** generation with **WeasyPrint** including all mandatory legal fields, tax summary,
  Verifactu legend, and QR code.
- **Email** delivery of the PDF (pluggable backend), recipient taken from the form or the client;
  `sent_at` timestamp and PII-free instrumentation.

### 📊 Tracking, listing & dashboard
- Invoice states: **draft → issued → sent**, via a derived status property.
- Owner-scoped listing (issued, non-annulled only) and a **detail view** with a submission-status
  badge (no record / pending / sent / accepted / rejected) and attempt history.
- Bootstrap 5 dashboard with navigation, quick actions, and an authenticated landing page.

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.13 |
| Framework | Django 5 |
| Database | PostgreSQL (SQLite fallback for local/tests) |
| Crypto | `cryptography` — AES-256-GCM at rest, PKCS#12 loading |
| Verifactu XML | `lxml` (build/validate), `signxml` (XAdES XML-DSig) |
| AEAT transport | `requests-pkcs12` (mutual-TLS SOAP) |
| PDF / QR | `weasyprint`, `segno` |
| Config | `python-dotenv` |

---

## Quick start

### Prerequisites
- Python 3.13+
- PostgreSQL (optional for local dev — SQLite is used automatically when `POSTGRES_DB` is unset)

### Setup

```bash
# Clone and enter the repo
cd es-invoices

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (see "Configuration" below)
cp .env.example .env               # then edit values

# Apply migrations and run
python3 manage.py migrate
python3 manage.py runserver
```

In `DEBUG` mode a dev-login shortcut is available at `/dev/login/` for fast local iteration.

### Run the tests

```bash
python3 manage.py test
```

> 231 tests cover all apps. Two PostgreSQL-gated tests (concurrent numbering / hash-chain locks)
> are skipped automatically on SQLite.

---

## Configuration

Configuration is loaded from environment variables (via `.env`). Key settings:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Core Django settings |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | PostgreSQL (omit `POSTGRES_DB` to use SQLite) |
| `CERT_ENCRYPTION_KEY` | Key for AES-256-GCM encryption of stored certificates |
| `AEAT_ENV`, `AEAT_SUBMISSION_LIVE`, `AEAT_SUBMISSION_TIMEOUT`, `AEAT_SUBMISSION_MAX_RETRIES` | AEAT submission behaviour (`LIVE` defaults OFF) |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | Email delivery |

See [`docs/deployment-runbook.md`](docs/deployment-runbook.md) for the full operator reference.

---

## Architecture

FacturaSimple is a **modular monolith** — a single deployable Django app partitioned into
focused modules, chosen for lean operability over microservice overhead:

```
accounts/      Registration, auth, account lifecycle
clients/       Client CRUD, B2B/B2C tax-ID validation
invoicing/     Invoice issuance, series, gap-free numbering
compliance/    Verifactu records, hash chain, XAdES signing  (isolated + versioned)
submission/    AEAT mTLS adapter, submission outcomes        (swappable behind an interface)
documents/     PDF rendering + email delivery
certificates/  Encrypted PKCS#12 certificate storage
config/        Django project settings & URLs
devtools/      DEBUG-only dev-login shim (never loaded in production)
```

**Design highlights**

- **Compliance isolation (AD-2):** all Verifactu rules live in one versioned module so spec
  changes are absorbed in one place.
- **Swappable AEAT adapter (AD-3):** direct mTLS-SOAP integration was proven via PoC, with a
  third-party gateway as a fallback behind the same interface.
- **Integrity guarantees:** gap-free numbering, an anti-tampering hash chain, and
  post-issuance immutability (corrections/cancellations recorded in separate fields).
- **RGPD by design:** EU data residency, encryption in transit (TLS/mTLS) and at rest
  (AES-256-GCM), least-privilege access, and automated retention/purge.

---

## Project status

**Construction phase complete**, with a **GO** decision toward the Transition (beta) phase:
all core features implemented, tested, and documented. Target metrics: first invoice in
**< 5 min**, **≥ 99 %** first-submission acceptance at the AEAT, and **≥ 50 %** first-week
activation.

---

## Documentation

- [`docs/presentacion-facturasimple.md`](docs/presentacion-facturasimple.md) — project presentation (Spanish)
- [`docs/deployment-runbook.md`](docs/deployment-runbook.md) — operator runbook
- [`docs/vision.md`](docs/vision.md), [`docs/architecture-notebook.md`](docs/architecture-notebook.md), [`docs/use-cases/`](docs/use-cases/) — vision, architecture, use cases
- [`docs/roadmap.md`](docs/roadmap.md) — work items and status

> This repository follows the **OpenUP** engineering process. See [`.claude/CLAUDE.md`](.claude/CLAUDE.md)
> and [`docs-eng-process/`](docs-eng-process/) for the agent workflow and process docs.

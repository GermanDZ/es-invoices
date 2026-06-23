---
type: work-item
id: LOCAL-SETUP-001
status: approved
traces-from: [REQ-001]
verified-by: []
---

# Local Setup Guide — FacturaSimple

For production deployment see `docs/deployment-runbook.md`.  
This guide covers a local development environment: SQLite, DEBUG mode, no TLS, no real AEAT submissions.

---

## Prerequisites

- Python 3.10 or later (`python3 --version`)
- `pip` and `venv` (bundled with Python 3.10+)
- **No PostgreSQL required** — the app falls back to SQLite automatically when `POSTGRES_DB` is unset

---

## One-time setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the environment template
cp .env.example .env
```

The default `.env.example` values work out of the box for local development:
- `DJANGO_DEBUG=1` — enables the dev-login shortcut and `devtools` app
- `POSTGRES_DB=` (empty) — SQLite fallback, no database server needed
- `AEAT_SUBMISSION_LIVE=0` — no real tax-authority submissions

The only value you must generate is `CERT_ENCRYPTION_KEY`:

```bash
python3 -c "from certificates.crypto import generate_key; print(generate_key())"
```

Paste the output into `.env` as `CERT_ENCRYPTION_KEY=<value>`.

---

## Run the development server

> **Note:** `setup_local.sh` can't activate the venv in your shell (a child process
> can't modify the parent shell's environment). Always activate it yourself before
> running `manage.py` commands.

```bash
# Activate the venv (required every new shell session)
source .venv/bin/activate

# Apply database migrations (creates db.sqlite3 on first run)
python manage.py migrate

# Create the dev user (username: dev, password: dev)
python manage.py seed_dev_owner

# Start the server
python manage.py runserver
```

Open <http://localhost:8000/dev/login/> — this auto-logs-in as the dev user (DEBUG only).

---

## Environment variables reference

| Variable | Default in .env.example | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | `change-me-in-production` | Fine for local; change for any shared environment |
| `DJANGO_DEBUG` | `1` | Must be `0` in production |
| `DJANGO_ALLOWED_HOSTS` | *(empty)* | Not enforced when `DEBUG=1`; set to your domain in production |
| `CERT_ENCRYPTION_KEY` | *(empty — must generate)* | AES-256-GCM key for certificate storage; required at startup |
| `POSTGRES_DB` | *(empty)* | Leave empty to use SQLite; set all five `POSTGRES_*` vars for PostgreSQL |
| `AEAT_SUBMISSION_LIVE` | `0` | Set to `1` only in production with a real AEAT certificate loaded |
| `EMAIL_BACKEND` | *(not set — defaults to console)* | Emails print to the terminal in dev; set SMTP vars for real delivery |

---

## Running tests

```bash
# All tests (~220 cases, ~5 s on SQLite)
python manage.py test

# Single app
python manage.py test invoicing

# Smoke tests only
python manage.py test devtools.tests.test_smoke
```

Two Postgres-gated tests are automatically skipped when `POSTGRES_DB` is unset — this is expected.

---

## Interactive setup script

`scripts/setup_local.sh` automates the one-time setup steps above:

```bash
bash scripts/setup_local.sh
```

It will:
1. Verify Python 3.10+
2. Create `.venv` and install requirements
3. Generate and write `CERT_ENCRYPTION_KEY` to `.env` if missing
4. Run `migrate`
5. Run `seed_dev_owner`
6. Print the dev-login URL

---

## Troubleshooting

**`CERT_ENCRYPTION_KEY` error at startup**

```bash
python3 -c "from certificates.crypto import generate_key; print(generate_key())"
# Add the result to .env as CERT_ENCRYPTION_KEY=<value>
```

**`ModuleNotFoundError` for lxml, weasyprint, etc.**  
The venv is not active, or `pip install` was not run:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**PDF generation fails with a WeasyPrint error on macOS**  
WeasyPrint needs Pango. Install via Homebrew:
```bash
brew install pango
```

**`/dev/login/` returns 404**  
`DJANGO_DEBUG` must be `1` in `.env`. The devtools URLs are only registered when `DEBUG=True`.

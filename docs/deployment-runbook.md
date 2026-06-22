---
type: work-item
id: DEPLOY-001
status: approved
traces-from: [REQ-001]
verified-by: []
---

# Deployment Operator Runbook — FacturaSimple

**Version**: v1 (T-030)  
**Audience**: Operator deploying FacturaSimple to a production or beta environment.  
**Cross-reference**: `docs/rgpd-checklist.md` — RGPD compliance evidence.

---

## Prerequisites

Before starting:

- A Linux server (or VM) in an **EU-resident** cloud region (Hetzner Falkenstein/Helsinki,
  OVH Gravelines/Strasbourg, Scaleway Paris/Amsterdam — per AD-4).
- A domain name with DNS pointing to the server.
- A PostgreSQL 14+ database reachable from the app server (EU-resident, same provider).
- Python 3.11+ and `pip` available, or Docker if using a containerised deployment.
- A valid **AEAT qualified certificate** (PKCS#12 `.p12` / `.pfx`) for Verifactu
  submissions — uploaded via the product UI after first login.
- An SMTP provider with a send-only API key and a confirmed EU data-processing DPA
  (e.g. Brevo EU, Mailpace EU, or self-hosted Postfix).

---

## Step 1 — Clone and Install

```bash
git clone <repo-url> /srv/facturasimple
cd /srv/facturasimple
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 2 — Environment Variables

Create `/srv/facturasimple/.env` (or export into the process environment). **Never commit
this file.**

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | **Yes** | 50+ char random string. `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | **Yes** | Set to `0` (or omit — defaults to `False` in non-DEBUG mode). Never `1` in production. |
| `DATABASE_URL` | **Yes** | PostgreSQL DSN: `postgres://user:pass@host:5432/dbname` |
| `CERT_ENCRYPTION_KEY` | **Yes** | 32-byte base64-encoded AES key for user certificate encryption. `python3 -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"` |
| `AEAT_SUBMISSION_LIVE` | **Yes** | Set to `1` to enable real AEAT submissions. Defaults to `0` (disabled) — do not forget this for production. |
| `AEAT_ENDPOINT` | No | Override AEAT endpoint URL. Defaults to the AEAT production URL. |
| `EMAIL_BACKEND` | No | Defaults to `django.core.mail.backends.smtp.EmailBackend`. |
| `EMAIL_HOST` | **Yes** | SMTP hostname (e.g. `smtp.brevo.com`). |
| `EMAIL_PORT` | **Yes** | SMTP port — typically `587` (STARTTLS) or `465` (SSL). |
| `EMAIL_HOST_USER` | **Yes** | SMTP username / API key. |
| `EMAIL_HOST_PASSWORD` | **Yes** | SMTP password / API key secret. |
| `EMAIL_USE_TLS` | **Yes** | Set to `1` for STARTTLS (port 587). |
| `EMAIL_USE_SSL` | No | Set to `1` for SSL (port 465). Mutually exclusive with `EMAIL_USE_TLS`. |
| `DEFAULT_FROM_EMAIL` | **Yes** | Sender address, e.g. `noreply@yourdomain.com`. |
| `ALLOWED_HOSTS` | **Yes** | Comma-separated allowed hostnames, e.g. `facturasimple.example.com`. |

---

## Step 3 — Database Setup

### 3a. Create a least-privilege PostgreSQL user

Connect as the `postgres` superuser and run:

```sql
CREATE USER facturasimple WITH PASSWORD 'strong-password-here';
CREATE DATABASE facturasimple_prod OWNER facturasimple;
-- If using an existing DB server, grant only what is needed:
GRANT CONNECT ON DATABASE facturasimple_prod TO facturasimple;
GRANT USAGE ON SCHEMA public TO facturasimple;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO facturasimple;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO facturasimple;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO facturasimple;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO facturasimple;
-- Migrations need CREATE TABLE:
GRANT CREATE ON SCHEMA public TO facturasimple;
```

### 3b. Confirm SSL mode

Ensure the managed DB service enforces TLS for all connections, **or** add
`sslmode=require` to `DATABASE_URL`:

```
DATABASE_URL=postgres://facturasimple:pass@db.host:5432/facturasimple_prod?sslmode=require
```

### 3c. Run migrations

```bash
source .venv/bin/activate
python manage.py migrate
```

---

## Step 4 — TLS + Reverse Proxy

Set up **nginx** (or **Caddy**) to terminate TLS before the Django WSGI process.
`SECURE_SSL_REDIRECT = True` is set in `config/settings.py` for non-DEBUG environments —
this redirects plain HTTP to HTTPS at the Django layer, but TLS termination must happen
at the proxy.

### Caddy (simplest — auto TLS via Let's Encrypt)

```caddyfile
facturasimple.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

### nginx (manual cert)

```nginx
server {
    listen 443 ssl;
    server_name facturasimple.example.com;
    ssl_certificate     /etc/letsencrypt/live/facturasimple.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/facturasimple.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
server {
    listen 80;
    server_name facturasimple.example.com;
    return 301 https://$host$request_uri;
}
```

---

## Step 5 — First-Run Checks

Run the Django system check in deployment mode — **must report 0 critical warnings**:

```bash
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python manage.py check --deploy
```

Expected output includes warnings about HSTS subdomains and X-Content-Type-Options that
are acceptable; **no `CRITICAL` lines** should appear.

---

## Step 6 — Static Files + First Start

```bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

Use a process supervisor (systemd, supervisor) to keep gunicorn running. A minimal
systemd unit:

```ini
[Unit]
Description=FacturaSimple
After=network.target

[Service]
User=www-data
WorkingDirectory=/srv/facturasimple
EnvironmentFile=/srv/facturasimple/.env
ExecStart=/srv/facturasimple/.venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 --workers 3
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## Step 7 — Smoke Test

1. Open `https://facturasimple.example.com/` in a browser → redirects to login page ✅
2. Register a new account with a valid email + strong password.
3. Upload the AEAT certificate (`.p12`) via the certificate management page.
4. Create a test client (B2B, with CIF).
5. Issue a test invoice (1 line item, 21% IVA) → verify PDF downloads.
6. Submit to AEAT (with `AEAT_SUBMISSION_LIVE=1`) → verify `Correcto` or `pending` outcome.

---

## Step 8 — Post-Launch Follow-Ups

| Task | Description | Timing |
|---|---|---|
| T-028 | Configure `purge_expired_data` cron (automated retention) | Before production scale |
| T-029 | Enable self-service account deletion UI | Before broad user rollout |
| RGPD §1 | Confirm cloud provider EU region + obtain email provider DPA reference | Before first real user data |

---

## RGPD Cross-Check

All operator responsibilities from `docs/rgpd-checklist.md` are fulfilled by the steps
above. After completing this runbook, verify against the checklist §1–§4 ⚠️ items:

- § 1 EU residency — cloud provider + email DPA confirmed ✅
- § 2 Encryption in transit — TLS via reverse proxy + `EMAIL_USE_TLS=1` ✅
- § 3 Encryption at rest — `CERT_ENCRYPTION_KEY` set, block storage encryption confirmed ✅
- § 4 Least-privilege — DB grant SQL applied ✅

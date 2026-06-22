---
type: work-item
id: RGPD-001
status: active
traces-from: [T-026, R-06]
verified-by: [T-026]
---

# RGPD Pre-Launch Checklist — FacturaSimple

**Version**: v1 (T-026)
**Date**: 2026-06-22
**Author**: Developer role (T-026)
**Scope**: R-06 mitigation — five data-protection control areas required before launch.
**Status legend**: ✅ Compliant | ⚠️ Partial / operator responsibility | ❌ Blocking gap

No item is ❌ at task completion. Every ⚠️ has a named follow-up.

---

## 1. EU Data Residency

*AD-4 mandates EU-resident hosting (Hetzner / OVH / Scaleway). All datastores and
sub-processors that handle personal or fiscal data must be EU-resident.*

| Item | Status | Notes / Follow-up |
|------|--------|-------------------|
| App server hosted in EU region | ⚠️ | Operator responsibility: confirm EU datacenter at deploy time (AD-4 mandates Hetzner / OVH / Scaleway EU region). No code enforces this; verify in cloud console before launch. |
| PostgreSQL database hosted in EU | ⚠️ | Operator responsibility: same provider / region selection as app server. Confirm `POSTGRES_HOST` resolves to an EU endpoint at deploy time. |
| Sub-processor — email delivery | ⚠️ | Email backend is config (`EMAIL_BACKEND` env). Operator must choose an EU-resident SMTP provider (e.g. Brevo EU, Mailpace EU) or a self-hosted relay. Confirm provider's EU data-processing DPA before launch. |
| Sub-processor — no US-only SaaS used | ✅ | No third-party analytics, tracking, or CDN configured. AEAT endpoint is an official Spanish tax authority server (EU). |
| Data transfer outside EU | ✅ | No cross-border transfer is coded. AEAT submissions go to prewww1/www2.aeat.es (Spain/EU). |

**Follow-up**: Operator runbook step: document the chosen cloud provider + region + email provider's DPA reference before go-live. No code task required.

---

## 2. Encryption in Transit

*Django must enforce HTTPS in production via `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`, and `SECURE_HSTS_SECONDS`. All four are now present in `config/settings.py`
under `if not DEBUG:` so local development is unaffected.*

| Item | Status | Notes / Follow-up |
|------|--------|-------------------|
| `SECURE_SSL_REDIRECT = True` | ✅ | Added under `if not DEBUG:` guard in `config/settings.py` (T-026). |
| `SESSION_COOKIE_SECURE = True` | ✅ | Added under `if not DEBUG:` guard (T-026). |
| `CSRF_COOKIE_SECURE = True` | ✅ | Added under `if not DEBUG:` guard (T-026). |
| `SECURE_HSTS_SECONDS = 31536000` | ✅ | Added under `if not DEBUG:` guard (T-026). 1-year HSTS. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | ⚠️ | Not set. Operator should add if all subdomains are served over HTTPS. Low risk for v1 single-domain deployment; add in a follow-up if subdomains are provisioned. |
| TLS termination at load balancer / reverse proxy | ⚠️ | Operator responsibility: provision TLS certificate (Let's Encrypt) and configure nginx/Caddy to terminate HTTPS before the Django WSGI process. `SECURE_SSL_REDIRECT` assumes TLS is available. |
| AEAT API calls over HTTPS + client-cert mTLS | ✅ | `submission` adapter uses `requests` with `cert=` (mTLS); AEAT endpoints are HTTPS only (T-013/T-014). |
| Email delivery over TLS | ⚠️ | `EMAIL_USE_TLS` defaults `0`; operator must set `EMAIL_USE_TLS=1` (or `EMAIL_USE_SSL=1`) and configure a TLS-capable SMTP provider. Follow-up: operator runbook. |

---

## 3. Encryption at Rest

*Three layers: application-layer certificate encryption, cloud provider block-storage
encryption, and database connection SSL.*

| Item | Status | Notes / Follow-up |
|------|--------|-------------------|
| User certificates encrypted at app layer | ✅ | `certificates.crypto` uses AES-256-GCM with a per-encrypt fresh nonce; key loaded from `CERT_ENCRYPTION_KEY` env (fails loudly if missing — no silent plaintext fallback). Implemented T-011. |
| `CERT_ENCRYPTION_KEY` distinct from `SECRET_KEY` | ✅ | Deliberately separate key (T-011 design). Rotation of one does not expose the other. |
| Cloud provider block-storage encryption | ⚠️ | Operator responsibility: Hetzner/OVH/Scaleway all offer encrypted block volumes by default in EU regions; confirm at deploy time. Follow-up: operator runbook step (no code needed). |
| Database connection SSL | ⚠️ | `DATABASES` config does not set `OPTIONS: {'sslmode': 'require'}`. Operator should confirm the managed DB service enforces TLS on all connections, or add `sslmode=require` to the DB options. Follow-up: operator runbook. |
| Django `SECRET_KEY` rotation | ⚠️ | Production `SECRET_KEY` must be set via `DJANGO_SECRET_KEY` env; the insecure dev default is caught by `manage.py check --deploy`. Operator must set before launch. No code change needed. |
| Invoice PDF / fiscal records at rest | ✅ | No PDFs are stored server-side (generated on demand); invoice data lives in PostgreSQL (block-storage encryption above). No additional app-layer encryption needed. |

---

## 4. Least-Privilege Access

*Database credentials, email service credentials, and app-level access scoping.*

| Item | Status | Notes / Follow-up |
|------|--------|-------------------|
| Database user scope: DML+DDL only, no superuser | ⚠️ | Operator responsibility: create a dedicated `facturasimple` PG user with `GRANT` on the app schema only; do not use the `postgres` superuser in production. Expected privilege: `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on app tables; `CREATE` for migrations. Follow-up: operator runbook SQL snippet. |
| Email service credentials: send-only scope | ⚠️ | SMTP credentials are send-only by nature (no inbox access). Operator must use an SMTP API key scoped to a single sender domain. Follow-up: operator runbook. |
| App-level data isolation: owner-scoped queries | ✅ | All views scope queries to `request.user`-owned records (`series__owner`, `client__owner`, etc. — T-021/T-022/T-024). Cross-owner 404 guards verified in tests. |
| `@login_required` on all user-facing views | ✅ | All production-surface views protected (T-021); the dev-only `devtools` shim is DEBUG-gated and cannot appear in production. |
| AEAT client certificate: limited scope | ✅ | Certificate is operator-issued (T-011 upload); it authenticates to AEAT only. Stored encrypted; single accessor in `certificates.services`. |

---

## 5. Data Retention Policy

*Legal basis, data categories, retention periods, and deletion approach for v1.*

FacturaSimple v1 processes the following personal and fiscal data categories under Spanish law:

| Data Category | Legal Basis | Retention Period | Deletion Approach |
|---------------|------------|-----------------|-------------------|
| Invoice records (NumSerie, amounts, issuer fiscal identity) | Legal obligation — Spanish tax law (Ley 58/2003 General Tributaria; Ley 37/1992 IVA) | **5 years** from issuance (standard audit window; confirm with tax advisor if 10-year obligation applies) | Manual deletion on account deletion for v1. Automated deletion follow-up: T-028. |
| Client personal data (name, NIF/NIE, address) | Contractual necessity (invoice recipient identification per AEAT) + legitimate interest | **5 years** (tied to invoice record retention) or until account deletion if shorter | Manual on account deletion (v1). T-028 follow-up. |
| User account data (email, password hash) | Contract (service provision) | Duration of active account + **30 days** post-deletion grace period | Operator-assisted manual deletion (v1). Self-service deletion UI follow-up: T-029. |
| AEAT submission attempt records (SubmissionAttempt) | Legal obligation (AEAT Verifactu compliance record) | **5 years** (same as invoice records) | Manual on account deletion (v1). T-028 follow-up. |
| Encrypted user certificates (PKCS#12) | Contract + legal obligation (AEAT mTLS auth) | Duration of active account | Cascading delete with `UserCertificate` model (`on_delete=CASCADE` on account — T-011). |

**Right to erasure (RGPD Art. 17):** Fiscal records are exempt from erasure where retention is legally required (Art. 17(3)(b)). Non-fiscal personal data must be erasable on request. v1 handles this via operator-assisted manual deletion; self-service is a post-launch follow-up (T-029).

**Data Protection Officer:** Not required for v1 (small-scale processing, no systematic monitoring). Operator must reassess if processing scale increases.

**Follow-up tasks:**
- T-028: Automated retention enforcement / scheduled deletion job (post-launch)
- T-029: Self-service account + data deletion UI (post-launch)

---

## 6. Summary

| Area | Overall Status | Open Follow-ups |
|------|---------------|-----------------|
| EU Data Residency | ⚠️ Operator responsibility | Confirm cloud provider + email DPA at deploy |
| Encryption in Transit | ✅ Code-side complete | Operator: TLS termination, EMAIL_USE_TLS, HSTS subdomains |
| Encryption at Rest | ⚠️ Partial | Operator: block-storage confirm, DB SSL, SECRET_KEY rotation |
| Least-Privilege Access | ⚠️ Operator responsibility | DB user grant SQL, email API key scope |
| Data Retention Policy | ✅ Documented | T-028 (automated deletion), T-029 (self-service deletion UI) |

**Launch gate**: No ❌ items. All ⚠️ items are operator-configuration responsibilities or named post-launch follow-up tasks.

**Next actions before go-live (operator runbook)**:
1. Confirm EU-region cloud provider + obtain email provider DPA.
2. Set production env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `CERT_ENCRYPTION_KEY`, `EMAIL_USE_TLS=1`, `AEAT_SUBMISSION_LIVE=1`.
3. Provision TLS certificate; configure reverse proxy to terminate HTTPS.
4. Create least-privilege PostgreSQL user; grant schema permissions.
5. Run `python manage.py check --deploy` — confirm 0 critical warnings.
6. Schedule post-launch T-028 (automated deletion) and T-029 (self-service deletion).

"""
Minimal Django settings for FacturaSimple (bootstrapped by T-011).

Datastore is PostgreSQL in deployed environments (AD-6, EU-resident per AD-4);
local/test runs fall back to SQLite when no POSTGRES_* env is set so the suite
runs without a server. Certificate material is encrypted at rest with a key read
from CERT_ENCRYPTION_KEY, deliberately distinct from SECRET_KEY (see
certificates.crypto).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from the project root before any _env() call. Already-set
# environment variables (e.g. from a systemd EnvironmentFile) take precedence.
load_dotenv(BASE_DIR / ".env", override=False)


def _env(name, default=None):
    return os.environ.get(name, default)


# SECURITY ---------------------------------------------------------------------
# A dev fallback keeps local runs friction-free; deployed environments MUST set
# DJANGO_SECRET_KEY (and DEBUG off).
SECRET_KEY = _env("DJANGO_SECRET_KEY", "dev-insecure-key-change-in-production")
DEBUG = _env("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in _env("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

# Key for at-rest certificate encryption (base64-encoded 32 bytes). No default:
# certificates.crypto raises if it is missing, so storage cannot silently run
# unencrypted. Tests provide their own via override_settings.
CERT_ENCRYPTION_KEY = _env("CERT_ENCRYPTION_KEY")

# APPLICATIONS -----------------------------------------------------------------
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
    "accounts",
]

# Dev-only shim (T-020): registered ONLY under DEBUG so its management command and
# /dev/ URLs cannot exist in production. There is intentionally no production auth
# surface here — the real login flow is a separate, future roadmap item. DEBUG in
# production is already a critical, separately-guarded misconfiguration.
if DEBUG:
    INSTALLED_APPS.append("devtools")

# Dev-login shortcut config (consumed only by the DEBUG-gated devtools app).
DEV_LOGIN_REDIRECT = _env("DEV_LOGIN_REDIRECT", "/clients/")
DEV_OWNER_USERNAME = _env("DEV_OWNER_USERNAME", "dev")
DEV_OWNER_PASSWORD = _env("DEV_OWNER_PASSWORD", "dev")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DATABASE ---------------------------------------------------------------------
# PostgreSQL (AD-6) when POSTGRES_DB is configured; SQLite otherwise so local
# and CI test runs need no server.
if _env("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _env("POSTGRES_DB"),
            "USER": _env("POSTGRES_USER", "postgres"),
            "PASSWORD": _env("POSTGRES_PASSWORD", ""),
            "HOST": _env("POSTGRES_HOST", "localhost"),
            "PORT": _env("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# AUTHENTICATION (T-021) -------------------------------------------------------
# Real product auth: email-as-username registration/login (accounts app), session
# via SessionMiddleware. LOGIN_URL is a named route so @login_required redirects
# anonymous users to the product login in every environment (the DEBUG-gated
# devtools shim is a separate dev-loop shortcut, not the gate target).
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:landing"
LOGOUT_REDIRECT_URL = "accounts:login"

# Django's four default validators, enabled for account creation (was empty
# during the engine-only phase; real registration now enforces them).
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# PRODUCTION SECURITY (T-026, RGPD/R-06) ----------------------------------------
# These settings enforce HTTPS and secure cookies in non-debug environments.
# All four are gated on `not DEBUG` so local development is unaffected.
# Kill-switch: remove or comment out these lines and redeploy (no data migration).
if not DEBUG:
    SECURE_SSL_REDIRECT = True          # Redirect all HTTP → HTTPS
    SESSION_COOKIE_SECURE = True        # Session cookies sent over HTTPS only
    CSRF_COOKIE_SECURE = True           # CSRF token cookies sent over HTTPS only
    SECURE_HSTS_SECONDS = 31536000      # 1-year HSTS (enables HTTPS preloading)

# AEAT SUBMISSION (T-014, AD-3) -------------------------------------------------
# The submission adapter only calls the AEAT when AEAT_SUBMISSION_LIVE is truthy
# — a config-read kill-switch (default OFF) so local/CI never reach the tax
# authority by accident. This is PERMANENT safety infrastructure, NOT a rollout
# flag: it must exist for the life of the product so non-production environments
# can never make a real, legally-effective submission. Do not "remove once rolled
# out" — there is no rolled-out state in which dev/CI should hit the live AEAT.
# AEAT_ENV selects the target; the endpoint defaults to the preproducción
# (sandbox) address and must be overridden explicitly for production, so
# production is never the default. See docs/changes/T-019/plan.md (reframe) and
# docs/changes/T-014/plan.md §Rollout.
AEAT_SUBMISSION_LIVE = _env("AEAT_SUBMISSION_LIVE", "0") == "1"
AEAT_ENV = _env("AEAT_ENV", "preproduccion")  # "preproduccion" | "produccion"
# Preproducción VERI*FACTU sending endpoint (prewww1 — sandbox, no tax effect).
AEAT_ENDPOINT = _env(
    "AEAT_ENDPOINT",
    "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP",
)
# Bounded transport retries on timeout / connection / HTTP 5xx (not on business
# rejections). 1 + this many retries are attempted before degrading to "pending".
AEAT_SUBMISSION_MAX_RETRIES = int(_env("AEAT_SUBMISSION_MAX_RETRIES", "3"))
AEAT_SUBMISSION_TIMEOUT = int(_env("AEAT_SUBMISSION_TIMEOUT", "45"))

# DOCUMENT & DELIVERY (T-016, S-3) ---------------------------------------------
# PDF generation + send-by-email. Email uses Django's pluggable backend so the
# concrete provider is config, not code: the console backend (default) prints to
# stdout for local/dev and never sends, while deployments set EMAIL_BACKEND to an
# SMTP backend and wire EMAIL_HOST/PORT/USER/PASSWORD via env. See
# docs/changes/T-016/plan.md §Rollout.
EMAIL_BACKEND = _env(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = _env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(_env("EMAIL_PORT", "25"))
EMAIL_HOST_USER = _env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = _env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _env("EMAIL_USE_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = _env("DEFAULT_FROM_EMAIL", "no-reply@facturasimple.example")

# Base URL of the AEAT VERI*FACTU public QR-verification service embedded on the
# invoice PDF. Defaults to the preproducción (sandbox) address so a misconfigured
# deployment never silently points consumers at the wrong host; production must
# override it explicitly (prewww → www2). The QR encodes this base + the invoice's
# persisted NIF / NumSerie / FechaExpedicion / ImporteTotal (compliance values).
VERIFACTU_QR_BASE_URL = _env(
    "VERIFACTU_QR_BASE_URL",
    "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR",
)

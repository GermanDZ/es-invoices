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

BASE_DIR = Path(__file__).resolve().parent.parent


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
    "invoicing",
    "compliance",
]

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

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

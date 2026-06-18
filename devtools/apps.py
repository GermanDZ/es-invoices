"""App config for the dev-only shim (T-020).

Registered in INSTALLED_APPS only under DEBUG (see config/settings.py), so this
app — its management command and its /dev/ URLs — does not exist in production.
"""
from django.apps import AppConfig


class DevtoolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "devtools"

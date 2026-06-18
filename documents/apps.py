from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Document & delivery module (architecture-notebook §4) — PDF + email.

    A read-only consumer of the invoicing core: it renders an already-issued
    invoice to a PDF and delivers it. No models, so no migrations.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "documents"

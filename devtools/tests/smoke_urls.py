"""URL conf for smoke tests — wires all product routes unconditionally.

config.urls gates /dev/ on DEBUG, which Django's test runner forces to False at
urlconf-load time. Smoke tests use this urlconf via override_settings so every
route is available regardless of the DEBUG flag.
"""
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
    path("invoices/", include("invoicing.urls")),
    path("submissions/", include("submission.urls")),
    path("dev/", include("devtools.urls")),
    path("", RedirectView.as_view(url="/dev/login/", permanent=False)),
]

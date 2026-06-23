"""Test urlconf wiring the dev routes unconditionally (T-020).

``config.urls`` gates these on DEBUG, which Django's test runner forces to False
at urlconf-load time — so the routes never register under ``manage.py test``.
Happy-path tests swap in this urlconf via ``override_settings(ROOT_URLCONF=...)``
to assert the wiring, and drive the view's own ``settings.DEBUG`` guard
separately. This mirrors the production block in config.urls.
"""
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("login/", include("accounts.urls")),
    path("invoices/", include("invoicing.urls")),
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
    path("submission/", include("submission.urls")),
    path("dev/", include("devtools.urls")),
    path("", RedirectView.as_view(url="/dev/login/", permanent=False)),
]

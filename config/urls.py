"""Root URL configuration for FacturaSimple."""
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
    # Real product auth (T-021): registration, login, logout, and the
    # authenticated landing at "/". Available in every environment.
    path("", include("accounts.urls")),
]

if settings.DEBUG:
    # Dev-only (T-020): a one-click browser login shortcut kept for the fast
    # inner dev loop. The production landing/login now own "/" (accounts.urls),
    # so the old DEBUG root→/dev/login redirect is gone; only the /dev/ shortcut
    # routes stay DEBUG-gated (a cold-started prod process never registers them;
    # the dev_login view also guards on DEBUG itself).
    urlpatterns += [
        path("dev/", include("devtools.urls")),
    ]

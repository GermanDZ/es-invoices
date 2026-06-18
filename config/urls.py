"""Root URL configuration for FacturaSimple."""
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
]

if settings.DEBUG:
    # Dev-only (T-020): a one-click browser login and a root that points at it.
    # No production landing page is defined here — that is a separate roadmap
    # item. Both routes vanish when DEBUG is off (a cold-started prod process
    # never registers them); the dev_login view also guards on DEBUG itself.
    from django.views.generic.base import RedirectView

    urlpatterns += [
        path("dev/", include("devtools.urls")),
        path("", RedirectView.as_view(url="/dev/login/", permanent=False)),
    ]

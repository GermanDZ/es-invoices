"""Root URL configuration for FacturaSimple."""
from django.urls import include, path

urlpatterns = [
    path("certificate/", include("certificates.urls")),
    path("clients/", include("clients.urls")),
]

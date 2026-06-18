"""URL routes for the certificate onboarding flow (T-011 Operation 5)."""
from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.upload, name="upload"),
    path("delete/", views.delete, name="delete"),
]

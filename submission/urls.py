"""URL routes for the AEAT submission UI (T-023, UC-002)."""
from django.urls import path

from . import views

app_name = "submission"

urlpatterns = [
    path("invoice/<int:invoice_pk>/submit/", views.submission_submit, name="submit"),
]

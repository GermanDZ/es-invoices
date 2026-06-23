"""URL routes for the invoice issuance UI (T-022 Operation 4)."""
from django.urls import path

from . import views

app_name = "invoicing"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("new/", views.invoice_create, name="create"),
    path("<int:pk>/", views.invoice_detail, name="detail"),
    path("<int:pk>/pdf/", views.invoice_pdf, name="pdf"),
    path("<int:pk>/send/", views.invoice_send, name="send"),
    path("<int:pk>/rectificar/", views.invoice_rectificar, name="rectificar"),
    path("<int:pk>/anular/", views.invoice_annul, name="annul"),
]

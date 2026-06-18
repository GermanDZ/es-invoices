"""Dev-only URLs (T-020). Included from config/urls.py only under DEBUG."""
from django.urls import path

from . import views

app_name = "devtools"

urlpatterns = [
    path("login/", views.dev_login, name="login"),
]

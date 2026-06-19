"""Auth routes (T-021): landing, registration, login, and logout.

Login/logout are Django's built-in class-based views configured with the
email-based form and project templates; registration and landing are local.
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailAuthenticationForm

app_name = "accounts"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=EmailAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    # Django 5 disallows GET logout — the landing template POSTs to this route.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

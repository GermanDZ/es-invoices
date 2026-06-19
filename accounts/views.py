"""Authentication views (T-021): registration plus the authenticated landing.

Login and logout reuse Django's built-in class-based views (wired in urls.py);
only registration and the landing need custom handling.
"""
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:landing")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:landing")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def landing(request):
    return render(request, "accounts/landing.html")

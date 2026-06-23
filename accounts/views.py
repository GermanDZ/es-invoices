"""Authentication views (T-021): registration plus the authenticated landing.

Login and logout reuse Django's built-in class-based views (wired in urls.py);
only registration and the landing need custom handling.

Self-service account deletion (T-029, RGPD Art. 17):
  ``delete_account_confirm`` — GET: info page; POST: marks account for deletion.
  ``delete_account_done``    — landing shown immediately after the request is
                                accepted (user is already logged out by then).
"""
import logging

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import RegistrationForm
from .models import DeletionRequest

logger = logging.getLogger(__name__)


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
    return redirect("invoicing:list")


@login_required
def delete_account_confirm(request):
    """Step 1 (GET) + Step 2 (POST) of the self-service deletion flow.

    GET  — render a page explaining what will be deleted and what will be
           retained, with a final confirm button.
    POST — create a :class:`~accounts.models.DeletionRequest`, set the account
           to inactive (blocks immediate re-login), cascade-delete certificates
           via the existing ``on_delete=CASCADE`` relationship (T-011), terminate
           the session, send a confirmation email, and redirect to the done page.

    Idempotent: a second POST from the same user (e.g. a back-button submit)
    does nothing harmful — ``get_or_create`` is used so we do not overwrite the
    original timestamp.
    """
    if request.method == "POST":
        user = request.user
        email = user.email

        # 1. Create deletion request (idempotent — do not reset the timestamp).
        DeletionRequest.objects.get_or_create(
            user=user,
            defaults={"requested_at": timezone.now()},
        )

        # 2. Mark account inactive immediately (blocks login from this point on).
        user.is_active = False
        user.save(update_fields=["is_active"])

        # 3. Terminate the current session before the user object is de-activated.
        logout(request)

        # 4. Send confirmation email (RGPD right-to-erasure acknowledgement).
        #    Failures are logged but never fatal — the deletion request is already
        #    persisted; the user has been logged out and the account deactivated.
        try:
            send_mail(
                subject="Solicitud de eliminación de cuenta — FacturaSimple",
                message=(
                    "Hemos recibido tu solicitud de eliminación de cuenta.\n\n"
                    "Tu cuenta ha sido desactivada de inmediato. Tus datos personales "
                    "serán eliminados definitivamente en un plazo de 30 días, conforme "
                    "al artículo 17 del RGPD.\n\n"
                    "Los registros fiscales (facturas emitidas) se conservarán durante "
                    "el periodo legalmente exigido (5 años) sin datos de carácter "
                    "personal adicionales.\n\n"
                    "Si no realizaste esta solicitud, contacta con soporte inmediatamente."
                ),
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Could not send deletion confirmation email to %s", email
            )

        return redirect("accounts:delete_account_done")

    # GET — informational confirmation page.
    return render(request, "accounts/delete_account_confirm.html")


def delete_account_done(request):
    """Public landing shown after the deletion request has been accepted.

    The user is already logged out at this point; the page must be public so the
    redirect after ``logout()`` does not bounce back to the login gate.
    """
    return render(request, "accounts/delete_account_done.html")

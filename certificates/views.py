"""Certificate onboarding views (T-011 Operations 4 & 5).

Upload / replace / delete for the logged-in user's qualified certificate. These
views never decrypt or log certificate material — they delegate storage and
status to ``certificates.services`` (least-privilege, requirement 6).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from . import services
from .forms import CertificateUploadForm


@login_required
def upload(request):
    if request.method == "POST":
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            services.store_certificate(
                request.user,
                p12_bytes=form.cleaned_data["_p12_bytes"],
                passphrase=form.cleaned_data["_passphrase"],
                subject=form.cleaned_data["_subject"],
                not_after=form.cleaned_data["_not_after"],
            )
            messages.success(request, "Certificate stored securely.")
            return redirect("certificates:upload")
    else:
        form = CertificateUploadForm()

    return render(
        request,
        "certificates/upload.html",
        {
            "form": form,
            "status": services.certificate_status(request.user),
            "configured": services.certificate_status(request.user) == "configured",
        },
    )


@login_required
def delete(request):
    if request.method == "POST":
        services.delete_certificate(request.user)
        messages.success(request, "Certificate deleted.")
    return redirect("certificates:upload")

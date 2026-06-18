"""Upload form with PKCS#12 validation (T-011 Operation 4).

Validation depth per the spec assumption: the file must load as PKCS#12 with the
supplied passphrase, must contain *both* a private key and a certificate, and the
certificate must not be expired. Full qualified-CA / FNMT trust-chain validation
is deferred. On success the parsed material is stashed on ``cleaned_data`` for the
view to hand to ``certificates.services`` — the form never persists or logs it.
"""
from cryptography.hazmat.primitives.serialization import pkcs12
from django import forms
from django.utils import timezone


class CertificateUploadForm(forms.Form):
    certificate_file = forms.FileField(
        label="Qualified certificate (.p12 / .pfx)",
        help_text="Your PKCS#12 file containing the certificate and private key.",
    )
    passphrase = forms.CharField(
        label="Certificate passphrase",
        widget=forms.PasswordInput,
        required=False,
        strip=False,
    )

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("certificate_file")
        passphrase = cleaned.get("passphrase") or ""
        if upload is None:
            return cleaned

        data = upload.read()
        pw = passphrase.encode() if passphrase else None
        try:
            key, cert, _extra = pkcs12.load_key_and_certificates(data, pw)
        except (ValueError, TypeError):
            # Wrong passphrase or not a valid PKCS#12 container both land here;
            # keep the message generic so it never leaks which it was.
            raise forms.ValidationError(
                "Could not load the certificate. Check the file is a valid "
                "PKCS#12 (.p12/.pfx) and the passphrase is correct."
            )

        if key is None or cert is None:
            raise forms.ValidationError(
                "The PKCS#12 file must contain both a certificate and its "
                "private key."
            )

        if cert.not_valid_after_utc <= timezone.now():
            raise forms.ValidationError("This certificate has expired.")

        # Stash parsed values for the view -> services. Underscore-prefixed so
        # they are clearly out-of-band of the declared form fields.
        cleaned["_p12_bytes"] = data
        cleaned["_passphrase"] = passphrase
        cleaned["_subject"] = cert.subject.rfc4514_string()
        cleaned["_not_after"] = cert.not_valid_after_utc
        return cleaned

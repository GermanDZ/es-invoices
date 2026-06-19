"""Authentication forms for the product (T-021).

Email is the account identifier (spec Assumption 1): registration creates a
``User`` whose ``username`` is the lower-cased email, and login authenticates by
email. No custom user model — Django's default ``auth.User`` is sufficient for
the single-operator scope (scope.md D-3).
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegistrationForm(forms.Form):
    """Open self-service registration: email + password + confirmation.

    Enforces email uniqueness (one account per email — scope N-5 single-operator),
    password match, and Django's configured ``AUTH_PASSWORD_VALIDATORS``.
    """

    email = forms.EmailField(label="Email")
    password1 = forms.CharField(
        label="Contraseña", widget=forms.PasswordInput, strip=False
    )
    password2 = forms.CharField(
        label="Repite la contraseña", widget=forms.PasswordInput, strip=False
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if p1:
            # Validate against an unsaved user so UserAttributeSimilarityValidator
            # can compare the password to the chosen email.
            email = cleaned.get("email", "")
            probe = User(username=email, email=email)
            try:
                validate_password(p1, probe)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        email = self.cleaned_data["email"]
        return User.objects.create_user(
            username=email, email=email, password=self.cleaned_data["password1"]
        )


class EmailAuthenticationForm(AuthenticationForm):
    """Login by email — the ``username`` field is relabeled and normalized so the
    credential entered matches the email-as-username records RegistrationForm
    creates."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget = forms.EmailInput(attrs={"autofocus": True})

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

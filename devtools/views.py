"""Dev-only browser login shortcut (T-020).

Get-or-creates the single dev owner and logs them into the browser session, so a
developer on a fresh checkout can reach the @login_required product pages without
``manage.py shell`` + ``force_login``. Guarded on DEBUG so it can never
authenticate a session in production (belt-and-suspenders with the DEBUG-gated
app registration in config/settings.py).
"""
from django.conf import settings
from django.contrib.auth import login
from django.http import Http404
from django.shortcuts import redirect

from .owner import get_or_create_dev_owner

# The dev owner comes from get_or_create (no authenticate() call), so it carries
# no ``backend`` attribute; login() needs it named explicitly.
_BACKEND = "django.contrib.auth.backends.ModelBackend"


def dev_login(request):
    if not settings.DEBUG:
        raise Http404
    user, _ = get_or_create_dev_owner()
    login(request, user, backend=_BACKEND)
    return redirect(settings.DEV_LOGIN_REDIRECT)

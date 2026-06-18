"""Least-privilege static check (T-011 Operation 7, requirement 6).

Confirms structurally that decryption of certificate material is confined to
``certificates.services`` — no view, form, model, or other app module calls
``crypto.decrypt`` or otherwise emits plaintext. This is the deterministic form
of the spec's "grep the code paths" verification step.
"""
import pathlib

from django.test import SimpleTestCase

APP_DIR = pathlib.Path(__file__).resolve().parent.parent
# crypto.py *defines* decrypt; services.py is the sanctioned *caller*.
ALLOWED = {"crypto.py", "services.py"}


class LeastPrivilegeTests(SimpleTestCase):
    def _app_modules(self):
        for path in APP_DIR.glob("*.py"):
            if path.name in ALLOWED:
                continue
            yield path

    def test_only_services_decrypts(self):
        # Match the call form ``decrypt(`` — not the bare word, which legitimately
        # appears in module docstrings describing the least-privilege rule.
        offenders = [
            path.name
            for path in self._app_modules()
            if "decrypt(" in path.read_text()
        ]
        self.assertEqual(
            offenders,
            [],
            f"plaintext decryption must be confined to services.py; "
            f"found a decrypt reference in {offenders}",
        )

"""Requirement 1 — the versioned module interface (AD-2/R-01)."""
import compliance
from django.test import SimpleTestCase


class ModuleInterfaceTests(SimpleTestCase):
    def test_module_version_exposed(self):
        self.assertRegex(compliance.MODULE_VERSION, r"^\d+\.\d+\.\d+$")

    def test_public_api_reachable_without_private_submodule_import(self):
        # The public verbs resolve off the package itself (lazy), so a caller
        # never imports compliance.records / .signing / .services directly.
        self.assertTrue(callable(compliance.generate_alta))
        self.assertTrue(callable(compliance.generate_anulacion))
        self.assertTrue(callable(compliance.validate_issuable))
        for name in ("generate_alta", "generate_anulacion", "validate_issuable"):
            self.assertIn(name, dir(compliance))

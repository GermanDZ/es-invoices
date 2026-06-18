"""Spanish tax-id validation — DNI/NIE/CIF checksum (T-015 requirement 2/3)."""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from clients.validation import is_valid_spanish_taxid, validate_spanish_taxid


class SpanishTaxIdTests(SimpleTestCase):
    def test_valid_dni(self):
        self.assertTrue(is_valid_spanish_taxid("12345678Z"))

    def test_valid_nie(self):
        self.assertTrue(is_valid_spanish_taxid("X1234567L"))

    def test_valid_cif(self):
        self.assertTrue(is_valid_spanish_taxid("A58818501"))

    def test_normalises_case_and_separators(self):
        self.assertTrue(is_valid_spanish_taxid(" 12345678-z "))

    def test_bad_dni_control_letter(self):
        self.assertFalse(is_valid_spanish_taxid("12345678A"))

    def test_bad_cif_control(self):
        self.assertFalse(is_valid_spanish_taxid("A58818500"))

    def test_garbage_rejected(self):
        self.assertFalse(is_valid_spanish_taxid("NOPE123"))

    def test_empty_rejected(self):
        self.assertFalse(is_valid_spanish_taxid(""))

    def test_validator_raises_on_invalid(self):
        with self.assertRaises(ValidationError):
            validate_spanish_taxid("12345678A")

    def test_validator_passes_on_valid(self):
        # Should not raise.
        validate_spanish_taxid("12345678Z")

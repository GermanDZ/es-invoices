"""Spanish tax-id validation for client records (T-015 Operation 2).

Validates the three Spanish fiscal identifier formats a client may carry:

* **DNI** — 8 digits + a control letter (residents / sole traders).
* **NIE** — X/Y/Z + 7 digits + a control letter (foreign residents).
* **CIF / NIF-entity** — an organisation letter + 7 digits + a control char
  (companies and other legal entities).

The check is **format + control-character checksum** — the deterministic,
offline validation the T-015 spec assumes, **not** a live AEAT existence lookup.
``validate_spanish_taxid`` raises ``django.core.exceptions.ValidationError`` so
the model and form layers reject a bad id uniformly (requirement 2 / 3).
"""
import re

from django.core.exceptions import ValidationError

# DNI/NIE control letter: indexed by (number mod 23).
_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
# NIE leading letter maps to a digit prefix before the mod-23 check.
_NIE_PREFIX = {"X": "0", "Y": "1", "Z": "2"}
# CIF control char (when a letter) indexed by the computed control digit.
_CIF_CONTROL_LETTERS = "JABCDEFGHI"
# Organisation letters whose control char MUST be a letter / MUST be a digit;
# any other valid org letter accepts either form.
_CIF_LETTER_ONLY = set("PQSNW")
_CIF_DIGIT_ONLY = set("ABEH")
_CIF_FIRST_LETTERS = set("ABCDEFGHJNPQRSUVW")

_DNI_RE = re.compile(r"^(\d{8})([A-Z])$")
_NIE_RE = re.compile(r"^([XYZ])(\d{7})([A-Z])$")
_CIF_RE = re.compile(r"^([A-Z])(\d{7})([0-9A-J])$")


def _dni_letter(number: int) -> str:
    return _DNI_LETTERS[number % 23]


def _check_dni(value: str) -> bool:
    m = _DNI_RE.match(value)
    return bool(m) and _dni_letter(int(m.group(1))) == m.group(2)


def _check_nie(value: str) -> bool:
    m = _NIE_RE.match(value)
    if not m:
        return False
    prefix, digits, letter = m.groups()
    return _dni_letter(int(_NIE_PREFIX[prefix] + digits)) == letter


def _check_cif(value: str) -> bool:
    m = _CIF_RE.match(value)
    if not m:
        return False
    org, digits, control = m.groups()
    if org not in _CIF_FIRST_LETTERS:
        return False
    total = 0
    for i, ch in enumerate(digits):
        n = int(ch)
        if i % 2 == 0:  # odd positions (1,3,5,7) doubled, then digit-summed
            n *= 2
            n = n // 10 + n % 10
        total += n
    control_digit = (10 - (total % 10)) % 10
    control_letter = _CIF_CONTROL_LETTERS[control_digit]
    if org in _CIF_LETTER_ONLY:
        return control == control_letter
    if org in _CIF_DIGIT_ONLY:
        return control == str(control_digit)
    return control in (str(control_digit), control_letter)


def normalize_taxid(value: str) -> str:
    """Upper-case and strip separators/whitespace for a stable comparison."""
    return (value or "").strip().upper().replace("-", "").replace(" ", "")


def is_valid_spanish_taxid(value: str) -> bool:
    v = normalize_taxid(value)
    if not v:
        return False
    return _check_dni(v) or _check_nie(v) or _check_cif(v)


def validate_spanish_taxid(value) -> None:
    """Django validator — raise ``ValidationError`` for a bad ES tax-id."""
    if not is_valid_spanish_taxid(value):
        raise ValidationError(
            "Enter a valid Spanish tax ID (DNI, NIE or CIF) with a correct "
            "control character."
        )

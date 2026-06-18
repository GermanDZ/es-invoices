"""Compliance / Verifactu module (AD-2) — the single versioned home for every
Verifactu/AEAT rule.

Callers (e.g. the T-014 submission adapter) use **only** this public API and
never import the private submodules (``records``, ``signing``, ``services``,
``validation``). ``MODULE_VERSION`` lets each persisted record record which
ruleset produced it, so a spec change (R-01) is an explicit, isolated version
bump here.

The callables are resolved lazily (PEP 562 ``__getattr__``) so importing this
package at Django app-load time does not pull in the ORM models before the app
registry is ready.
"""
import importlib

MODULE_VERSION = "1.0.0"

_LAZY = {
    "generate_alta": ("compliance.services", "generate_alta"),
    "generate_anulacion": ("compliance.services", "generate_anulacion"),
    "validate_issuable": ("compliance.validation", "validate_issuable"),
}

__all__ = ["MODULE_VERSION", *list(_LAZY)]


def __getattr__(name):
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        return getattr(importlib.import_module(module_name), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)

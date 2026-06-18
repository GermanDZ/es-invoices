"""AD-3 — the AEAT VERI*FACTU submission gateway (T-014).

This app is the submission boundary: a :class:`~submission.gateway.SubmissionGateway`
interface with one direct AEAT adapter behind it. It takes a signed
``compliance.VerifactuRecord`` (AD-2 / T-013), submits it over mutual-TLS SOAP using
the user's qualified certificate (T-011), and records the per-record outcome. A
gateway adapter can later be swapped in behind the same interface (AD-3, R-03's
pre-agreed fallback) without touching call sites.
"""

"""Submit one VerifactuRecord to the AEAT via the configured gateway (T-014).

The cert-gated preproducción **smoke path**: run it against a record whose owner has
a real qualified certificate stored, with ``AEAT_SUBMISSION_ENABLED=1`` and
``AEAT_ENDPOINT`` pointing at the sandbox, to confirm the end-to-end transport. It
refuses cleanly (no call) when the kill-switch is off — so it is safe to wire into
CI/local where the flag defaults off. It is also the seed for a future scheduled
re-drive of ``pending`` attempts.

    python manage.py aeat_submit <record_id>

RGPD: prints only the status / AEAT code / CSV — never NIF, name, or cert material.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from compliance.models import VerifactuRecord
from submission import services


class Command(BaseCommand):
    help = "Submit a VerifactuRecord to the AEAT and print its outcome."

    def add_arguments(self, parser):
        parser.add_argument("record_id", type=int)

    def handle(self, *args, **opts):
        if not getattr(settings, "AEAT_SUBMISSION_ENABLED", False):
            raise CommandError(
                "AEAT_SUBMISSION_ENABLED is off — refusing to submit. "
                "Set it (and AEAT_ENDPOINT) to run the preproducción smoke."
            )
        try:
            record = VerifactuRecord.objects.get(pk=opts["record_id"])
        except VerifactuRecord.DoesNotExist as exc:
            raise CommandError(f"No VerifactuRecord with id {opts['record_id']}") from exc

        outcome = services.submit_record(record)
        self.stdout.write(
            f"env={getattr(settings, 'AEAT_ENV', '?')} status={outcome.status.value} "
            f"estado={outcome.estado or '—'} code={outcome.aeat_code or '—'} "
            f"csv={outcome.csv or '—'} retries={outcome.retries}"
        )

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.complaints.models import Complaint, StatusEvent
from apps.workflow.services import transition


class Command(BaseCommand):
    help = "Return unanswered information requests to triage after the configured timeout."

    def handle(self, *args, **options):
        days = getattr(settings, "INFO_REQUEST_TIMEOUT_DAYS", 14)
        if not isinstance(days, int) or days < 1:
            raise CommandError("INFO_REQUEST_TIMEOUT_DAYS must be a positive integer.")
        cutoff = timezone.now() - timedelta(days=days)
        expired = 0
        candidates = Complaint.objects.filter(status=Complaint.Status.INFO_REQUESTED).iterator()
        for complaint in candidates:
            latest_event = StatusEvent.objects.filter(complaint=complaint).order_by("-created_at", "-pk").first()
            if not latest_event or latest_event.to_status != Complaint.Status.INFO_REQUESTED or latest_event.created_at > cutoff:
                continue
            reason = f"no reply within {days} days"
            try:
                transition(
                    complaint,
                    Complaint.Status.IN_TRIAGE,
                    actor=None,
                    reason=reason,
                    timeout=True,
                )
            except ValidationError:
                # A concurrent citizen reply may have already returned this complaint to triage.
                continue
            expired += 1
        self.stdout.write(f"Expired {expired} information request(s).")

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.complaints.models import Complaint
from apps.workflow.services import flag_sla_breach


class Command(BaseCommand):
    help = "Flag overdue active SLA clocks and notify the responsible supervisors."

    def handle(self, *args, **options):
        now = timezone.now()
        candidate_ids = Complaint.objects.filter(
            due_at__lte=now,
            sla_paused_at__isnull=True,
            sla_breached_at__isnull=True,
        ).exclude(
            status__in=[
                Complaint.Status.INFO_REQUESTED,
                Complaint.Status.VERIFIED_CLOSED,
                Complaint.Status.REJECTED,
                Complaint.Status.CANCELLED,
            ]
        ).order_by("due_at", "pk").values_list("pk", flat=True)
        flagged = 0
        for complaint_id in candidate_ids.iterator(chunk_size=200):
            with transaction.atomic():
                complaint = Complaint.objects.select_for_update().get(pk=complaint_id)
                if flag_sla_breach(complaint, now=now):
                    flagged += 1
        self.stdout.write(f"Flagged {flagged} SLA breach(es).")

from django.db.models import Q

from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint
from apps.workflow.permissions import can_view_audit


def visible_audit_events(user):
    if not can_view_audit(user):
        return AuditEvent.objects.none()
    events = AuditEvent.objects.select_related("actor")
    if user.role == "supervisor":
        # Restrict event object IDs and complaint references to reports visible in the supervisor's department.
        complaint_ids = list(Complaint.objects.visible_to(user).values_list("pk", flat=True))
        complaint_id_strings = [str(complaint_id) for complaint_id in complaint_ids]
        events = events.filter(
            Q(object_type="Complaint", object_id__in=complaint_id_strings)
            | Q(after__complaint_id__in=complaint_ids)
        )
    return events.order_by("-created_at", "-pk")

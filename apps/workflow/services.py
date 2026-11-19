from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, ComplaintMessage, StatusEvent

# One table controls every valid status transition; later days add console actions through this service.
TRANSITIONS = {
    ("submitted", "in_triage"): {"system"},
    ("in_triage", "info_requested"): {"triage_reviewer"},
    ("info_requested", "in_triage"): {"citizen", "system"},
    ("in_triage", "routed"): {"triage_reviewer", "admin"},
    ("in_triage", "rejected"): {"triage_reviewer", "admin"},
    ("routed", "acknowledged"): {"department_official", "supervisor"},
    ("routed", "in_triage"): {"department_official", "supervisor"},
    ("acknowledged", "assigned"): {"department_official", "supervisor"},
    ("assigned", "in_progress"): {"field_worker"},
    ("in_progress", "resolved_pending_verification"): {"field_worker", "department_official"},
    ("resolved_pending_verification", "verified_closed"): {"supervisor", "citizen"},
    ("resolved_pending_verification", "reopened"): {"supervisor", "citizen"},
    ("reopened", "assigned"): {"supervisor"},
    ("submitted", "cancelled"): {"citizen"},
    ("in_triage", "cancelled"): {"citizen"},
    ("routed", "cancelled"): {"citizen"},
}


@transaction.atomic
def transition(complaint, to_status, actor=None, reason=None, **data):
    locked = Complaint.objects.select_for_update().get(pk=complaint.pk)
    role = actor.role if actor else "system"
    allowed_roles = TRANSITIONS.get((locked.status, to_status), set())
    if role not in allowed_roles:
        raise ValidationError("This status transition is not allowed.")
    if (locked.status, to_status) == ("in_triage", "info_requested") and not data.get("message"):
        raise ValidationError("An information request message is required.")
    if (locked.status, to_status) == ("info_requested", "in_triage") and not (data.get("reply") or data.get("timeout")):
        raise ValidationError("A citizen reply or timeout is required.")
    if to_status in {"rejected", "reopened"} and not reason:
        raise ValidationError("A reason is required.")
    if (locked.status, to_status) in {("in_triage", "routed"), ("acknowledged", "assigned"), ("reopened", "assigned")}:
        if not data.get("department") and not getattr(locked, "department_id", None):
            raise ValidationError("A department is required.")
    if (locked.status, to_status) == ("in_progress", "resolved_pending_verification"):
        if not locked.evidence.filter(kind="field_after").exists() or not data.get("note"):
            raise ValidationError("After evidence and a note are required.")
    if (locked.status, to_status) == ("resolved_pending_verification", "verified_closed") and not data.get("method"):
        raise ValidationError("A verification method is required.")
    if (locked.status, to_status) == ("routed", "in_triage") and not reason:
        raise ValidationError("A transfer reason is required.")
    if actor and role == "admin" and not reason:
        raise ValidationError("An administrator override requires a reason.")
    if (locked.status, to_status) == ("in_triage", "rejected") and not data.get("reason_code"):
        raise ValidationError("A reason code is required.")
    if (locked.status, to_status) == ("in_triage", "routed") and not data.get("rule_version"):
        raise ValidationError("A routing rule version is required.")
    if (locked.status, to_status) in {("acknowledged", "assigned"), ("reopened", "assigned")}:
        assignee = data.get("assignee")
        if not assignee:
            raise ValidationError("An assignee is required.")
        if locked.department_id and assignee.department_id != locked.department_id:
            raise ValidationError("The assignee must belong to the complaint department.")

    previous = locked.status
    locked.status = to_status
    for field in ("department", "assignee"):
        if field in data:
            setattr(locked, field, data[field])
    locked.save()
    StatusEvent.objects.create(complaint=locked, from_status=previous, to_status=to_status, actor=actor, role=role, reason=reason or "")
    AuditEvent.objects.create(actor=actor, role=role, action="status_transition", object_type="Complaint", object_id=str(locked.pk), before={"status": previous}, after={"status": to_status}, reason=reason or "")
    message_body = data.get("message") if to_status == "info_requested" else data.get("reply") if previous == "info_requested" and to_status == "in_triage" else None
    if message_body:
        message = ComplaintMessage.objects.create(complaint=locked, author=actor, body=message_body)
        AuditEvent.objects.create(actor=actor, role=role, action="complaint_message_added", object_type="ComplaintMessage", object_id=str(message.pk), after={"complaint_id": locked.pk, "body": message_body})
    return locked

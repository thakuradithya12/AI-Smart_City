from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, ComplaintMessage, Evidence, Resolution, StatusEvent
from apps.complaints.services import delete_private_files, store_citizen_image
from apps.geography.models import RoutingRule

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


def active_routing_rule(complaint):
    # Ward-specific active routing rules take precedence over all-ward defaults.
    rules = RoutingRule.objects.filter(
        category=complaint.category,
        effective_from__lte=timezone.now(),
    ).order_by("-version")
    ward_rule = rules.filter(ward_id=complaint.ward_id).first() if complaint.ward_id else None
    return ward_rule or rules.filter(ward__isnull=True).first()


@transaction.atomic
def route_complaint(complaint, actor, department_override=None, reason=None):
    locked = Complaint.objects.select_for_update().select_related("category").get(pk=complaint.pk)
    if locked.status != Complaint.Status.IN_TRIAGE:
        raise ValidationError("Only complaints in triage can be routed.")
    rule = active_routing_rule(locked)
    if rule is None:
        raise ValidationError("No active ward or category routing rule is configured.")
    department = department_override or rule.department
    reason = (reason or "").strip()
    overridden = department.pk != rule.department_id
    if overridden and not reason:
        raise ValidationError("A reason is required when overriding the routing rule.")
    if actor.role == "admin" and not reason:
        raise ValidationError("An administrator routing decision requires a reason.")

    transition(
        locked,
        Complaint.Status.ROUTED,
        actor=actor,
        reason=reason if overridden or actor.role == "admin" else None,
        department=department,
        rule_version=rule.version,
    )
    AuditEvent.objects.create(
        actor=actor,
        role=actor.role,
        action="complaint_routed",
        object_type="Complaint",
        object_id=str(locked.pk),
        after={
            "department_id": department.pk,
            "routing_rule_version": rule.version,
            "overridden": overridden,
        },
        reason=reason if overridden or actor.role == "admin" else "",
    )
    return locked


def add_field_evidence(complaint, actor, upload, kind):
    paths = []
    try:
        with transaction.atomic():
            locked = Complaint.objects.select_for_update().get(pk=complaint.pk)
            if actor.role != "field_worker" or locked.assignee_id != actor.pk:
                raise ValidationError("Only the assigned field worker can add work evidence.")
            if locked.status != Complaint.Status.IN_PROGRESS:
                raise ValidationError("Work evidence can only be added while work is in progress.")
            if kind not in {Evidence.Kind.FIELD_BEFORE, Evidence.Kind.FIELD_AFTER}:
                raise ValidationError("Choose a before or after work photo.")

            original_path, display_path, digest = store_citizen_image(upload)
            paths.extend((original_path, display_path))
            evidence = Evidence.objects.create(
                complaint=locked,
                kind=kind,
                original_path=original_path,
                display_path=display_path,
                sha256=digest,
                uploaded_by=actor,
            )
            AuditEvent.objects.create(
                actor=actor,
                role=actor.role,
                action="evidence_uploaded",
                object_type="Evidence",
                object_id=str(evidence.pk),
                after={"complaint_id": locked.pk, "kind": kind, "sha256": digest},
            )
        return evidence
    except Exception:
        delete_private_files(paths)
        raise


@transaction.atomic
def transition(complaint, to_status, actor=None, reason=None, **data):
    locked = Complaint.objects.select_for_update().get(pk=complaint.pk)
    role = actor.role if actor else "system"
    allowed_roles = TRANSITIONS.get((locked.status, to_status), set())
    if role not in allowed_roles:
        raise ValidationError("This status transition is not allowed.")
    if actor and not Complaint.objects.visible_to(actor).filter(pk=locked.pk).exists():
        raise ValidationError("This user cannot act on this complaint.")
    if (locked.status, to_status) == ("in_triage", "info_requested") and not data.get("message"):
        raise ValidationError("An information request message is required.")
    if (locked.status, to_status) == ("info_requested", "in_triage") and not (data.get("reply") or data.get("timeout")):
        raise ValidationError("A citizen reply or timeout is required.")
    if to_status in {"rejected", "reopened"} or (locked.status, to_status) == ("routed", "in_triage") or role == "admin":
        if not reason or not 5 <= len(reason.strip()) <= 500:
            raise ValidationError("A reason of 5 to 500 characters is required.")
    if (locked.status, to_status) in {("in_triage", "routed"), ("acknowledged", "assigned"), ("reopened", "assigned")}:
        if not data.get("department") and not getattr(locked, "department_id", None):
            raise ValidationError("A department is required.")
    if (locked.status, to_status) == ("in_progress", "resolved_pending_verification"):
        if not locked.evidence.filter(kind="field_after").exists() or not data.get("note", "").strip():
            raise ValidationError("After evidence and a note are required.")
    if (locked.status, to_status) == ("resolved_pending_verification", "verified_closed"):
        if not data.get("method"):
            raise ValidationError("A verification method is required.")
        if role == "citizen" and data["method"] != "citizen_confirmation":
            raise ValidationError("Citizen confirmation must be recorded as the verification method.")
        if role == "supervisor" and data["method"] != "site_review":
            raise ValidationError("Supervisor verification must use the site review method.")
    if (locked.status, to_status) == ("routed", "in_triage") and not reason:
        raise ValidationError("A transfer reason is required.")
    if actor and role == "admin" and not reason:
        raise ValidationError("An administrator override requires a reason.")
    if (locked.status, to_status) == ("in_triage", "rejected") and not reason:
        raise ValidationError("A rejection reason is required.")
    if (locked.status, to_status) == ("in_triage", "routed") and not data.get("rule_version"):
        raise ValidationError("A routing rule version is required.")
    if (locked.status, to_status) in {("acknowledged", "assigned"), ("reopened", "assigned")}:
        assignee = data.get("assignee")
        if not assignee:
            raise ValidationError("An assignee is required.")
        if locked.department_id and assignee.department_id != locked.department_id:
            raise ValidationError("The assignee must belong to the complaint department.")

    previous = locked.status
    previous_department_id = locked.department_id
    resolution_before = None
    resolution_after = None
    locked.status = to_status
    # A transfer back to triage clears the prior department so its officials lose visibility.
    if (previous, to_status) == ("routed", "in_triage"):
        locked.department = None
    for field in ("department", "assignee"):
        if field in data:
            setattr(locked, field, data[field])
    locked.save()
    if (previous, to_status) == ("in_progress", "resolved_pending_verification"):
        prior_resolution = Resolution.objects.filter(complaint=locked).first()
        if prior_resolution:
            resolution_before = {
                "claimed_by_id": prior_resolution.claimed_by_id,
                "claimed_at": prior_resolution.claimed_at.isoformat(),
                "claim_note": prior_resolution.claim_note,
                "verified_by_id": prior_resolution.verified_by_id,
                "verified_at": prior_resolution.verified_at.isoformat() if prior_resolution.verified_at else None,
                "method": prior_resolution.method,
                "outcome": prior_resolution.outcome,
            }
        resolution, _created = Resolution.objects.update_or_create(
            complaint=locked,
            defaults={
                "claimed_by": actor,
                "claimed_at": timezone.now(),
                "claim_note": data["note"].strip(),
                "verified_by": None,
                "verified_at": None,
                "method": "",
                "outcome": "",
            },
        )
        resolution_after = {
            "claimed_by_id": resolution.claimed_by_id,
            "claimed_at": resolution.claimed_at.isoformat(),
            "claim_note": resolution.claim_note,
            "outcome": resolution.outcome,
        }
    elif (previous, to_status) in {
        ("resolved_pending_verification", "verified_closed"),
        ("resolved_pending_verification", "reopened"),
    }:
        resolution = Resolution.objects.select_for_update().get(complaint=locked)
        resolution_before = {
            "verified_by_id": resolution.verified_by_id,
            "verified_at": resolution.verified_at.isoformat() if resolution.verified_at else None,
            "method": resolution.method,
            "outcome": resolution.outcome,
        }
        resolution.verified_by = actor
        resolution.verified_at = timezone.now()
        resolution.method = data.get("method") or f"{role}_dispute"
        resolution.outcome = "verified" if to_status == "verified_closed" else "disputed"
        resolution.save(update_fields=["verified_by", "verified_at", "method", "outcome"])
        resolution_after = {
            "verified_by_id": resolution.verified_by_id,
            "verified_at": resolution.verified_at.isoformat(),
            "method": resolution.method,
            "outcome": resolution.outcome,
        }
    StatusEvent.objects.create(complaint=locked, from_status=previous, to_status=to_status, actor=actor, role=role, reason=reason or "")
    after = {"status": to_status}
    if (previous, to_status) == ("routed", "in_triage"):
        after["department_id"] = None
    if "department" in data:
        after["department_id"] = data["department"].pk
    if "assignee" in data:
        after["assignee_id"] = data["assignee"].pk
    if "rule_version" in data:
        after["routing_rule_version"] = data["rule_version"]
    if resolution_after:
        after["resolution"] = resolution_after
    before = {"status": previous, "department_id": previous_department_id}
    if resolution_before:
        before["resolution"] = resolution_before
    action = "admin_override" if role == "admin" else "status_transition"
    AuditEvent.objects.create(actor=actor, role=role, action=action, object_type="Complaint", object_id=str(locked.pk), before=before, after=after, reason=reason or "")
    message_body = data.get("message") if to_status == "info_requested" else data.get("reply") if previous == "info_requested" and to_status == "in_triage" else None
    if message_body:
        message = ComplaintMessage.objects.create(complaint=locked, author=actor, body=message_body)
        AuditEvent.objects.create(actor=actor, role=role, action="complaint_message_added", object_type="ComplaintMessage", object_id=str(message.pk), after={"complaint_id": locked.pk, "body": message_body})
    return locked

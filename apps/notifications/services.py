from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.complaints.models import Complaint, StatusEvent


TRANSITION_EVENTS = {
    ("submitted", "in_triage"): (Notification.Event.REPORT_RECEIVED, "citizen"),
    ("in_triage", "info_requested"): (Notification.Event.INFORMATION_REQUESTED, "citizen"),
    ("in_triage", "routed"): (Notification.Event.ROUTED, "citizen"),
    ("in_progress", "resolved_pending_verification"): (Notification.Event.WORK_CLAIMED, "citizen"),
    ("resolved_pending_verification", "verified_closed"): (Notification.Event.VERIFIED_CLOSED, "citizen"),
    ("resolved_pending_verification", "reopened"): (Notification.Event.REOPENED, "citizen"),
    ("acknowledged", "assigned"): (Notification.Event.ASSIGNED_TO_ME, "assignee"),
    ("reopened", "assigned"): (Notification.Event.ASSIGNED_TO_ME, "assignee"),
}


def _create_notification(recipient, event, complaint, status, source_key):
    if recipient is None:
        return None
    event_key = f"{source_key}:{recipient.pk}:{event}"
    # The unique source key makes retries of the workflow hook safe within and across commands.
    notification, _created = Notification.objects.get_or_create(
        event_key=event_key,
        defaults={
            "recipient": recipient,
            "event": event,
            "complaint": complaint,
            "status": status,
        },
    )
    return notification


def notify_transition(complaint, from_status, to_status, status_event):
    mapping = TRANSITION_EVENTS.get((from_status, to_status))
    if not mapping:
        return None
    event, target = mapping
    recipient = complaint.citizen if target == "citizen" else complaint.assignee
    return _create_notification(
        recipient,
        event,
        complaint,
        to_status,
        f"status:{status_event.pk}",
    )


def notify_assigned_worker(complaint, audit_event):
    return _create_notification(
        complaint.assignee,
        Notification.Event.ASSIGNED_TO_ME,
        complaint,
        complaint.status,
        f"audit:{audit_event.pk}",
    )


def notify_overdue_supervisors(complaint):
    if not complaint.department_id or not complaint.due_at:
        return []
    source_key = f"overdue:{complaint.pk}:{complaint.due_at.isoformat()}"
    return [
        _create_notification(
            supervisor,
            Notification.Event.OVERDUE,
            complaint,
            complaint.status,
            source_key,
        )
        for supervisor in User.objects.filter(
            department_id=complaint.department_id,
            role=User.Role.SUPERVISOR,
            is_active=True,
        ).order_by("pk")
    ]


def enqueue_citizen_reminders(*, now=None):
    """Queue one in-app/email reminder per work-completion status event after the delay."""
    current_time = now or timezone.now()
    cutoff = current_time - timedelta(days=settings.CITIZEN_REMINDER_DAYS)
    candidates = Complaint.objects.filter(
        status=Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        resolution__claimed_at__lte=cutoff,
    ).order_by("pk").values_list("pk", flat=True)
    created = 0
    for complaint_id in candidates.iterator(chunk_size=100):
        with transaction.atomic():
            # System maintenance uses row locks so concurrent scheduler instances cannot enqueue duplicates.
            complaint = Complaint.objects.select_for_update(skip_locked=True).filter(
                pk=complaint_id,
                status=Complaint.Status.RESOLVED_PENDING_VERIFICATION,
                resolution__claimed_at__lte=cutoff,
            ).select_related("resolution", "citizen").first()
            if complaint is None:
                continue
            claim_event = StatusEvent.objects.filter(
                complaint=complaint,
                to_status=Complaint.Status.RESOLVED_PENDING_VERIFICATION,
            ).order_by("-created_at", "-pk").first()
            if claim_event is None:
                continue
            _notification, was_created = Notification.objects.get_or_create(
                event_key=f"reminder:{claim_event.pk}:{complaint.citizen_id}:{Notification.Event.CITIZEN_REMINDER}",
                defaults={
                    "recipient": complaint.citizen,
                    "complaint": complaint,
                    "event": Notification.Event.CITIZEN_REMINDER,
                    "status": Complaint.Status.RESOLVED_PENDING_VERIFICATION,
                },
            )
            created += int(was_created)
    return created

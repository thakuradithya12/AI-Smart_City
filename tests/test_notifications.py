from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.complaints.models import Complaint, Evidence, Resolution
from apps.geography.models import Category, Department, Ward
from apps.notifications.models import Notification
from apps.notifications.services import notify_overdue_supervisors, notify_transition
from apps.workflow.services import transition


@pytest.fixture
def notification_setup(db):
    citizen = User.objects.create_user(
        email="notify-citizen@example.test", password="Strong!Password982", name="Notify Citizen"
    )
    worker = User.objects.create_user(
        email="notify-worker@example.test", password="Strong!Password982", name="Notify Worker",
        role=User.Role.FIELD_WORKER,
    )
    department = Department.objects.create(name="Notification Department")
    worker.department = department
    worker.save(update_fields=["department"])
    reviewer = User.objects.create_user(
        email="notify-reviewer@example.test", password="Strong!Password982", name="Notify Reviewer",
        role=User.Role.TRIAGE_REVIEWER,
    )
    official = User.objects.create_user(
        email="notify-official@example.test", password="Strong!Password982", name="Notify Official",
        role=User.Role.DEPARTMENT_OFFICIAL, department=department,
    )
    supervisor = User.objects.create_user(
        email="notify-supervisor@example.test", password="Strong!Password982", name="Notify Supervisor",
        role=User.Role.SUPERVISOR, department=department,
    )
    category = Category.objects.create(name="notification-test")
    polygon = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(
        name="Notification Test Ward",
        boundary=MultiPolygon(polygon, srid=4326),
        source="test-only synthetic polygon",
        effective_from=date(2026, 1, 1),
    )
    complaint = Complaint.objects.create(
        public_id="ASC-2026-000001",
        citizen=citizen,
        category=category,
        description="Private description must never appear in an email",
        location=Point(0, 0, srid=4326),
        ward=ward,
        consent_at="2026-01-01T00:00:00Z",
    )
    return SimpleNamespace(
        citizen=citizen, worker=worker, reviewer=reviewer, official=official,
        supervisor=supervisor, department=department, complaint=complaint,
    )


def test_development_uses_console_email_backend(settings):
    assert settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"


@pytest.mark.django_db
def test_report_received_notification_is_created_with_status_transition(notification_setup):
    setup = notification_setup

    transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=None)

    notification = Notification.objects.get()
    assert notification.recipient == setup.citizen
    assert notification.complaint == setup.complaint
    assert notification.event == Notification.Event.REPORT_RECEIVED
    assert notification.status == Complaint.Status.IN_TRIAGE


@pytest.mark.django_db
def test_notification_insert_rolls_back_with_failed_status_audit(notification_setup, monkeypatch):
    setup = notification_setup

    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit storage unavailable")

    class BrokenAuditManager:
        create = staticmethod(fail_audit)

    class BrokenAuditEvent:
        objects = BrokenAuditManager()

    monkeypatch.setattr("apps.workflow.services.AuditEvent", BrokenAuditEvent)
    with pytest.raises(RuntimeError, match="audit storage unavailable"):
        transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=None)

    setup.complaint.refresh_from_db()
    assert setup.complaint.status == Complaint.Status.SUBMITTED
    assert not Notification.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "before,after,event,recipient_name",
    [
        ("in_triage", "info_requested", Notification.Event.INFORMATION_REQUESTED, "citizen"),
        ("in_triage", "routed", Notification.Event.ROUTED, "citizen"),
        ("in_progress", "resolved_pending_verification", Notification.Event.WORK_CLAIMED, "citizen"),
        ("resolved_pending_verification", "verified_closed", Notification.Event.VERIFIED_CLOSED, "citizen"),
        ("resolved_pending_verification", "reopened", Notification.Event.REOPENED, "citizen"),
        ("acknowledged", "assigned", Notification.Event.ASSIGNED_TO_ME, "worker"),
        ("reopened", "assigned", Notification.Event.ASSIGNED_TO_ME, "worker"),
    ],
)
def test_transition_notification_event_and_recipient_are_deterministic(
    notification_setup, before, after, event, recipient_name
):
    setup = notification_setup
    setup.complaint.assignee = setup.worker
    status_event = SimpleNamespace(pk=42)

    notify_transition(setup.complaint, before, after, status_event)

    notification = Notification.objects.get()
    assert notification.event == event
    assert notification.recipient == getattr(setup, recipient_name)
    assert notification.status == after
    assert notification.event_key == f"status:42:{notification.recipient_id}:{event}"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "before,after,event,actor_name,extra",
    [
        ("in_triage", "info_requested", Notification.Event.INFORMATION_REQUESTED, "reviewer", {"message": "Please add more detail."}),
        ("in_triage", "routed", Notification.Event.ROUTED, "reviewer", {"department": "department", "rule_version": 1}),
        ("in_progress", "resolved_pending_verification", Notification.Event.WORK_CLAIMED, "worker", {"note": "Work is complete."}),
        ("resolved_pending_verification", "verified_closed", Notification.Event.VERIFIED_CLOSED, "supervisor", {"method": "site_review"}),
        ("resolved_pending_verification", "reopened", Notification.Event.REOPENED, "supervisor", {"reason": "Repair did not last."}),
        ("acknowledged", "assigned", Notification.Event.ASSIGNED_TO_ME, "official", {"department": "department", "assignee": "worker"}),
        ("reopened", "assigned", Notification.Event.ASSIGNED_TO_ME, "supervisor", {"department": "department", "assignee": "worker"}),
    ],
)
def test_status_transition_creates_expected_notification(
    notification_setup, before, after, event, actor_name, extra
):
    setup = notification_setup
    complaint = setup.complaint
    complaint.status = before
    if before in {"acknowledged", "in_progress", "resolved_pending_verification", "reopened"}:
        complaint.department = setup.department
    if before in {"in_progress", "reopened"}:
        complaint.assignee = setup.worker
    complaint.save(update_fields=["status", "department", "assignee"])
    if before == "in_progress":
        Evidence.objects.create(
            complaint=complaint, kind=Evidence.Kind.FIELD_AFTER, original_path="before/original.jpg",
            display_path="before/display.jpg", sha256="a" * 64, uploaded_by=setup.worker,
        )
    if before == "resolved_pending_verification":
        Resolution.objects.create(complaint=complaint, claimed_by=setup.worker, claim_note="Work recorded.")
    converted = {
        key: getattr(setup, value) if value in {"department", "worker"} else value
        for key, value in extra.items()
    }

    transition(
        complaint,
        after,
        actor=getattr(setup, actor_name),
        reason=converted.pop("reason", None),
        **converted,
    )

    notification = Notification.objects.get()
    assert notification.event == event
    assert notification.recipient == (setup.worker if event == Notification.Event.ASSIGNED_TO_ME else setup.citizen)
    assert notification.status == after


@pytest.mark.django_db
def test_transition_notification_hook_is_idempotent(notification_setup):
    setup = notification_setup
    status_event = SimpleNamespace(pk=88)

    notify_transition(setup.complaint, "in_triage", "routed", status_event)
    notify_transition(setup.complaint, "in_triage", "routed", status_event)

    assert Notification.objects.count() == 1


@pytest.mark.django_db
def test_overdue_notifications_go_only_to_department_supervisors(notification_setup):
    setup = notification_setup
    setup.complaint.department = setup.department
    setup.complaint.due_at = timezone.now() - timedelta(minutes=1)
    setup.complaint.save(update_fields=["department", "due_at"])
    other_department = Department.objects.create(name="Other Notification Department")
    User.objects.create_user(
        email="other-supervisor@example.test", password="Strong!Password982",
        name="Other Supervisor", role=User.Role.SUPERVISOR, department=other_department,
    )

    notices = notify_overdue_supervisors(setup.complaint)
    notify_overdue_supervisors(setup.complaint)

    assert len(notices) == 1
    assert Notification.objects.count() == 1
    assert Notification.objects.get().recipient == setup.supervisor
    assert Notification.objects.get().event == Notification.Event.OVERDUE


@pytest.mark.django_db
def test_notification_inbox_and_mark_read_are_private_to_recipient(
    client, notification_setup
):
    setup = notification_setup
    other = User.objects.create_user(
        email="other-notify@example.test", password="Strong!Password982", name="Other Citizen"
    )
    own_notice = Notification.objects.create(
        recipient=setup.citizen, complaint=setup.complaint, event=Notification.Event.REPORT_RECEIVED,
        status=Complaint.Status.IN_TRIAGE, event_key="inbox:own",
    )
    other_notice = Notification.objects.create(
        recipient=other, complaint=setup.complaint, event=Notification.Event.REPORT_RECEIVED,
        status=Complaint.Status.IN_TRIAGE, event_key="inbox:other",
    )
    client.force_login(setup.citizen)

    response = client.get(reverse("notifications_inbox"))
    assert response.status_code == 200
    assert b"ASC-2026-000001" in response.content
    assert b"Notifications" in response.content
    assert b"1 unread" in response.content
    assert response.context["unread_count"] == 1
    assert client.post(reverse("notification_mark_read", args=[other_notice.pk])).status_code == 404

    assert client.post(reverse("notification_mark_read", args=[own_notice.pk])).status_code == 302
    own_notice.refresh_from_db()
    assert own_notice.read_at is not None

    client.force_login(other)
    other_response = client.get(reverse("notifications_inbox"))
    assert other_response.status_code == 200
    assert b"ASC-2026-000001" not in other_response.content


@pytest.mark.django_db
@override_settings(SITE_BASE_URL="https://city.example.test")
def test_send_notifications_email_contains_only_public_id_status_and_link(
    notification_setup, monkeypatch
):
    setup = notification_setup
    setup.citizen.email = "citizen-private@example.test"
    setup.citizen.save(update_fields=["email"])
    notification = Notification.objects.create(
        recipient=setup.citizen, complaint=setup.complaint,
        event=Notification.Event.REPORT_RECEIVED, status=Complaint.Status.IN_TRIAGE,
        event_key="email:body",
    )
    sent = []
    monkeypatch.setattr(
        "apps.notifications.management.commands.send_notifications.send_mail",
        lambda **kwargs: sent.append(kwargs) or 1,
    )

    call_command("send_notifications")
    call_command("send_notifications")

    notification.refresh_from_db()
    assert notification.sent_at is not None
    assert notification.attempts == 1
    assert len(sent) == 1
    body = sent[0]["message"]
    assert body == f"ASC-2026-000001\nIn triage\nhttps://city.example.test{reverse('complaint_detail', args=[setup.complaint.pk])}"
    assert "Private description" not in body
    assert setup.citizen.name not in body
    if setup.citizen.phone_number:
        assert setup.citizen.phone_number not in body


@pytest.mark.django_db
@override_settings(NOTIFICATION_MAX_ATTEMPTS=3, NOTIFICATION_RETRY_DELAYS_SECONDS=(0, 0, 0))
def test_send_notifications_retries_then_caps_attempts_without_storing_pii(
    notification_setup, monkeypatch
):
    setup = notification_setup
    setup.citizen.email = "citizen-private@example.test"
    setup.citizen.save(update_fields=["email"])
    notification = Notification.objects.create(
        recipient=setup.citizen, complaint=setup.complaint,
        event=Notification.Event.REPORT_RECEIVED, status=Complaint.Status.IN_TRIAGE,
        event_key="email:retry",
    )
    attempts = []

    def fail_send(**kwargs):
        attempts.append(kwargs)
        raise RuntimeError("SMTP response mentions citizen-private@example.test")

    monkeypatch.setattr("apps.notifications.management.commands.send_notifications.send_mail", fail_send)
    for _ in range(4):
        call_command("send_notifications")

    notification.refresh_from_db()
    assert len(attempts) == 3
    assert notification.attempts == 3
    assert notification.sent_at is None
    assert notification.next_attempt_at is None
    assert notification.last_error == "RuntimeError"
    assert "citizen-private@example.test" not in notification.last_error


@pytest.mark.django_db
def test_notifications_without_email_remain_in_app_only(notification_setup):
    setup = notification_setup
    setup.citizen.email = ""
    setup.citizen.save(update_fields=["email"])
    notification = Notification.objects.create(
        recipient=setup.citizen, complaint=setup.complaint,
        event=Notification.Event.REPORT_RECEIVED, status=Complaint.Status.IN_TRIAGE,
        event_key="email:skip",
    )

    call_command("send_notifications")

    notification.refresh_from_db()
    assert notification.email_skipped_at is not None
    assert notification.attempts == 0
    assert notification.sent_at is None


@pytest.mark.django_db
@override_settings(NOTIFICATION_RETRY_DELAYS_SECONDS=(0, 0, 0))
def test_email_delivery_failure_does_not_roll_back_status_transition(notification_setup, monkeypatch):
    setup = notification_setup
    setup.citizen.email = "citizen-private@example.test"
    setup.citizen.save(update_fields=["email"])
    transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=None)
    monkeypatch.setattr(
        "apps.notifications.management.commands.send_notifications.send_mail",
        lambda **kwargs: (_ for _ in ()).throw(ConnectionError("SMTP offline")),
    )

    call_command("send_notifications")

    setup.complaint.refresh_from_db()
    assert setup.complaint.status == Complaint.Status.IN_TRIAGE
    notification = Notification.objects.get()
    assert notification.sent_at is None
    assert notification.attempts == 1

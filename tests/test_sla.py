from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint
from apps.geography.models import Category, Department, Ward
from apps.notifications.models import Notification
from apps.workflow.services import set_complaint_priority, transition


@pytest.fixture
def sla_setup(db):
    citizen = User.objects.create_user(email="sla-citizen@example.test", password="Strong!Password982", name="SLA Citizen")
    reviewer = User.objects.create_user(email="sla-reviewer@example.test", password="Strong!Password982", name="SLA Reviewer", role=User.Role.TRIAGE_REVIEWER)
    worker = User.objects.create_user(email="sla-worker@example.test", password="Strong!Password982", name="SLA Worker", role=User.Role.FIELD_WORKER)
    department = Department.objects.create(name="SLA Department")
    supervisor = User.objects.create_user(email="sla-supervisor@example.test", password="Strong!Password982", name="SLA Supervisor", role=User.Role.SUPERVISOR, department=department)
    worker.department = department
    worker.save(update_fields=["department"])
    category = Category.objects.create(name="sla-test", default_due_hours=24)
    polygon = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(name="SLA Test Ward", boundary=MultiPolygon(polygon, srid=4326), source="synthetic test fixture", effective_from=date(2026, 1, 1))
    complaint = Complaint.objects.create(public_id="ASC-2026-000002", citizen=citizen, category=category, location=Point(0, 0, srid=4326), ward=ward, department=department, due_at=timezone.now() + timedelta(days=1), consent_at="2026-01-01T00:00:00Z")
    return SimpleNamespace(citizen=citizen, reviewer=reviewer, worker=worker, supervisor=supervisor, department=department, complaint=complaint)


@pytest.mark.django_db
def test_info_request_pauses_and_reply_resumes_due_clock(sla_setup):
    setup = sla_setup
    transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=None)
    transition(setup.complaint, Complaint.Status.INFO_REQUESTED, actor=setup.reviewer, message="Please add details.")
    setup.complaint.refresh_from_db()
    paused_at = timezone.now() - timedelta(hours=2)
    setup.complaint.sla_paused_at = paused_at
    setup.complaint.save(update_fields=["sla_paused_at"])
    original_due = setup.complaint.due_at

    transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=setup.citizen, reply="Added details.")

    setup.complaint.refresh_from_db()
    assert setup.complaint.sla_paused_at is None
    assert setup.complaint.due_at >= original_due + timedelta(hours=2)


@pytest.mark.django_db
def test_reviewer_sets_priority_with_audit_and_ai_cannot_set_it(sla_setup):
    setup = sla_setup
    updated = set_complaint_priority(setup.complaint, setup.reviewer, "high", reason="Road is unsafe.")
    assert updated.priority == Complaint.Priority.HIGH
    event = AuditEvent.objects.latest("pk")
    assert event.action == "complaint_priority_changed"
    assert event.after["priority"] == "high"
    with pytest.raises(ValidationError):
        set_complaint_priority(updated, setup.worker, "urgent", reason="")


@pytest.mark.django_db
def test_check_sla_flags_and_notifies_once(sla_setup):
    setup = sla_setup
    setup.complaint.due_at = timezone.now() - timedelta(minutes=1)
    setup.complaint.save(update_fields=["due_at"])

    call_command("check_sla")
    call_command("check_sla")

    setup.complaint.refresh_from_db()
    assert setup.complaint.sla_breached_at is not None
    assert Notification.objects.filter(recipient=setup.supervisor, event=Notification.Event.OVERDUE).count() == 1
    assert AuditEvent.objects.filter(action="sla_breached", object_id=str(setup.complaint.pk)).count() == 1


@pytest.mark.django_db
def test_check_sla_does_not_flag_paused_or_terminal_complaints(sla_setup):
    setup = sla_setup
    transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=None)
    transition(setup.complaint, Complaint.Status.INFO_REQUESTED, actor=setup.reviewer, message="Please add details.")
    setup.complaint.refresh_from_db()
    setup.complaint.due_at = timezone.now() - timedelta(minutes=1)
    setup.complaint.save(update_fields=["due_at"])
    call_command("check_sla")
    setup.complaint.refresh_from_db()
    assert setup.complaint.sla_breached_at is None

    setup.complaint.due_at = timezone.now() + timedelta(days=1)
    setup.complaint.save(update_fields=["due_at"])
    transition(setup.complaint, Complaint.Status.IN_TRIAGE, actor=setup.citizen, reply="Added details.")
    transition(setup.complaint, Complaint.Status.REJECTED, actor=setup.reviewer, reason="Not a supported request.")
    setup.complaint.due_at = timezone.now() - timedelta(minutes=1)
    setup.complaint.save(update_fields=["due_at"])
    call_command("check_sla")
    setup.complaint.refresh_from_db()
    assert setup.complaint.sla_breached_at is None

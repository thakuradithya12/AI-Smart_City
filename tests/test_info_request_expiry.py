from datetime import date, timedelta

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.management import call_command
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, StatusEvent
from apps.accounts.models import User
from apps.geography.models import Category, Ward


@pytest.fixture
def expiry_setup(db):
    citizen = User.objects.create_user(
        email="expiry-citizen@example.test", password="Strong!Password982", name="Expiry Citizen"
    )
    reviewer = User.objects.create_user(
        email="expiry-reviewer@example.test", password="Strong!Password982",
        name="Expiry Reviewer", role=User.Role.TRIAGE_REVIEWER,
    )
    ring = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(
        name="Expiry Test Ward", boundary=MultiPolygon(ring, srid=4326),
        source="test-only synthetic polygon", effective_from=date(2026, 1, 1),
    )
    category = Category.objects.create(name="expiry-test")
    return {"citizen": citizen, "reviewer": reviewer, "ward": ward, "category": category}


@pytest.mark.django_db
def test_expire_info_requests_transitions_and_is_idempotent(expiry_setup, settings, capsys):
    setup = expiry_setup
    settings.INFO_REQUEST_TIMEOUT_DAYS = 10
    complaint = Complaint.objects.create(
        public_id="INFO-TIMEOUT", citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"],
        status=Complaint.Status.INFO_REQUESTED, consent_at=timezone.now(),
    )
    StatusEvent.objects.create(
        complaint=complaint, from_status="in_triage", to_status="info_requested",
        actor=setup["reviewer"], role="triage_reviewer", created_at=timezone.now() - timedelta(days=11),
    )
    call_command("expire_info_requests")
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_TRIAGE
    event = complaint.status_events.latest("created_at")
    assert event.actor is None and event.role == "system"
    assert event.reason == "no reply within 10 days"
    assert AuditEvent.objects.filter(action="status_transition", object_id=str(complaint.pk), role="system").exists()
    call_command("expire_info_requests")
    assert complaint.status_events.count() == 2


@pytest.mark.django_db
def test_timeout_is_not_applied_before_deadline_and_marker_is_shown(client, expiry_setup, settings):
    setup = expiry_setup
    settings.INFO_REQUEST_TIMEOUT_DAYS = 10
    complaint = Complaint.objects.create(
        public_id="INFO-NOT-DUE", citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"],
        status=Complaint.Status.INFO_REQUESTED, consent_at=timezone.now(),
    )
    StatusEvent.objects.create(
        complaint=complaint, from_status="in_triage", to_status="info_requested",
        actor=setup["reviewer"], role="triage_reviewer", created_at=timezone.now() - timedelta(days=2),
    )
    call_command("expire_info_requests")
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.INFO_REQUESTED

    timed_out = Complaint.objects.create(
        public_id="INFO-TIMED-OUT", citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"],
        status=Complaint.Status.IN_TRIAGE, consent_at=timezone.now(),
    )
    StatusEvent.objects.create(
        complaint=timed_out, from_status="info_requested", to_status="in_triage",
        actor=None, role="system", reason="no reply within 10 days",
    )
    client.force_login(setup["reviewer"])
    response = client.get("/console/triage/")
    assert b"Information request timed out" in response.content

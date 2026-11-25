from pathlib import Path

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.complaints.models import Complaint, Evidence, Resolution
from apps.geography.models import Category, Department
from apps.workflow.services import TRANSITIONS, transition
from scripts.generate_workflow_doc import OUTPUT, render


def test_every_complaint_status_is_reachable_from_submission():
    statuses = {status for status, _label in Complaint.Status.choices}
    reachable = {Complaint.Status.SUBMITTED}
    while True:
        next_statuses = {
            destination
            for (source, destination) in TRANSITIONS
            if source in reachable
        }
        expanded = reachable | next_statuses
        if expanded == reachable:
            break
        reachable = expanded
    assert reachable == statuses


def test_terminal_statuses_have_no_outgoing_transitions():
    terminal_statuses = {
        Complaint.Status.VERIFIED_CLOSED,
        Complaint.Status.REJECTED,
        Complaint.Status.CANCELLED,
    }
    assert not {source for source, _destination in TRANSITIONS} & terminal_statuses
    assert (Complaint.Status.REOPENED, Complaint.Status.ASSIGNED) in TRANSITIONS


def test_citizen_can_cancel_while_information_is_requested_before_acknowledgement():
    assert "citizen" in TRANSITIONS[(Complaint.Status.INFO_REQUESTED, Complaint.Status.CANCELLED)]


@pytest.fixture
def pending_resolution(db):
    department = Department.objects.create(name="Invariant Test Department")
    citizen = User.objects.create_user(
        email="invariant-citizen@example.test", password="Strong!Password982", name="Citizen"
    )
    worker = User.objects.create_user(
        email="invariant-worker@example.test", password="Strong!Password982", name="Worker",
        role=User.Role.FIELD_WORKER, department=department,
    )
    supervisor = User.objects.create_user(
        email="invariant-supervisor@example.test", password="Strong!Password982", name="Supervisor",
        role=User.Role.SUPERVISOR, department=department,
    )
    category = Category.objects.create(name="workflow-invariant", default_department=department)
    complaint = Complaint.objects.create(
        public_id="WORKFLOW-INVARIANT",
        citizen=citizen,
        category=category,
        department=department,
        assignee=worker,
        status=Complaint.Status.IN_PROGRESS,
        location=Point(78.48, 17.38, srid=4326),
        consent_at="2026-01-01T00:00:00Z",
    )
    Evidence.objects.create(
        complaint=complaint,
        kind=Evidence.Kind.FIELD_AFTER,
        original_path="private/original.jpg",
        display_path="private/display.jpg",
        sha256="0" * 64,
        uploaded_by=worker,
    )
    return complaint, worker, supervisor


@pytest.mark.django_db
def test_resolution_claim_and_verification_are_separate(pending_resolution):
    complaint, worker, supervisor = pending_resolution

    transition(
        complaint,
        Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        actor=worker,
        note="Replaced the damaged cover and cleared debris.",
    )
    resolution = Resolution.objects.get(complaint=complaint)
    assert resolution.claimed_by == worker
    assert resolution.claim_note == "Replaced the damaged cover and cleared debris."
    assert resolution.claimed_at is not None
    assert resolution.verified_by is None
    assert resolution.verified_at is None
    assert resolution.outcome == ""

    transition(
        complaint,
        Complaint.Status.VERIFIED_CLOSED,
        actor=supervisor,
        method="site_review",
    )
    resolution.refresh_from_db()
    assert resolution.claimed_by == worker
    assert resolution.verified_by == supervisor
    assert resolution.verified_at is not None
    assert resolution.outcome == "verified"


@pytest.mark.django_db
def test_citizen_silence_cannot_automatically_close_resolution(pending_resolution):
    complaint, worker, _supervisor = pending_resolution
    transition(
        complaint,
        Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        actor=worker,
        note="Repair completed; awaiting confirmation.",
    )

    with pytest.raises(ValidationError):
        transition(complaint, Complaint.Status.VERIFIED_CLOSED, actor=None, method="timeout")

    complaint.refresh_from_db()
    resolution = Resolution.objects.get(complaint=complaint)
    assert complaint.status == Complaint.Status.RESOLVED_PENDING_VERIFICATION
    assert resolution.verified_by is None
    assert resolution.verified_at is None


def test_generated_workflow_document_matches_source_tables():
    assert OUTPUT.read_text(encoding="utf-8") == render()
    source = Path(__file__).resolve().parents[1] / "apps/workflow/services.py"
    assert "TRANSITIONS" in source.read_text(encoding="utf-8")

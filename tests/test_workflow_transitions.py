import ast
from datetime import date
from pathlib import Path

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Evidence, Resolution, StatusEvent
from apps.geography.models import Category, Department, Ward
from apps.workflow.permissions import allowed_transition_targets, can_transition
from apps.workflow.services import TRANSITIONS, transition

APP_ROLES = [role for role, _label in User.Role.choices if role != User.Role.ADMIN]
ALL_ROLES = [*APP_ROLES, User.Role.ADMIN, "system"]
ALL_STATUSES = [status for status, _label in Complaint.Status.choices]


@pytest.fixture
def workflow_setup(db):
    department = Department.objects.create(name="Test Workflow Department")
    users = {}
    for index, role in enumerate(APP_ROLES + [User.Role.ADMIN]):
        users[role] = User.objects.create_user(
            email=f"workflow-{index}@example.test",
            password="Strong!Password982",
            name=f"Workflow {role}",
            role=role,
            department=department if role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR, User.Role.FIELD_WORKER} else None,
        )
    square = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(
        name="Workflow Test Ward",
        boundary=MultiPolygon(square, srid=4326),
        source="hand-written test polygon",
        effective_from=date(2026, 1, 1),
    )
    category = Category.objects.create(name="workflow-test", default_department=department)
    return {"department": department, "users": users, "ward": ward, "category": category}


def transition_data(pair, setup):
    department = setup["department"]
    users = setup["users"]
    data = {
        "department": department,
        "rule_version": 1,
        "reason_code": "not_supported",
        "assignee": users[User.Role.FIELD_WORKER],
        "method": "site_review",
        "message": "Please provide a nearby landmark.",
        "reply": "The location is beside the library.",
        "note": "Work recorded for the test.",
    }
    reason = "Required test reason."
    return data, reason


@pytest.mark.django_db
def test_every_status_pair_and_role_matches_transition_table(workflow_setup):
    setup = workflow_setup
    citizen = setup["users"][User.Role.CITIZEN]

    # Exercise every table pair and role with a row in the matching source status.
    for from_index, from_status in enumerate(ALL_STATUSES):
        for to_index, to_status in enumerate(ALL_STATUSES):
            complaint = Complaint.objects.create(
                public_id=f"TEST-{from_index:02}-{to_index:02}",
                citizen=citizen,
                category=setup["category"],
                location=Point(0, 0, srid=4326),
                ward=setup["ward"],
                department=setup["department"] if from_status not in {Complaint.Status.SUBMITTED, Complaint.Status.IN_TRIAGE} else None,
                assignee=setup["users"][User.Role.FIELD_WORKER] if from_status in {Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS} else None,
                status=from_status,
                consent_at="2026-01-01T00:00:00Z",
            )
            if from_status == Complaint.Status.IN_PROGRESS:
                Evidence.objects.create(
                    complaint=complaint,
                    kind=Evidence.Kind.FIELD_AFTER,
                    original_path="test/original.jpg",
                    display_path="test/display.jpg",
                    sha256="0" * 64,
                    uploaded_by=setup["users"][User.Role.FIELD_WORKER],
                )
            if from_status == Complaint.Status.RESOLVED_PENDING_VERIFICATION:
                Resolution.objects.create(
                    complaint=complaint,
                    claimed_by=setup["users"][User.Role.FIELD_WORKER],
                    claim_note="The repair work is recorded.",
                )
            data, reason = transition_data((from_status, to_status), setup)
            successful_roles = 0
            for role in ALL_ROLES:
                actor = None if role == "system" else setup["users"][role]
                expected = role in TRANSITIONS.get((from_status, to_status), set())
                role_data = dict(data)
                if to_status == Complaint.Status.VERIFIED_CLOSED and role == User.Role.CITIZEN:
                    role_data["method"] = "citizen_confirmation"
                if (from_status, to_status) == (Complaint.Status.INFO_REQUESTED, Complaint.Status.IN_TRIAGE) and role == "system":
                    role_data["reply"] = None
                    role_data["timeout"] = True
                if actor:
                    visible = Complaint.objects.visible_to(actor).filter(pk=complaint.pk).exists()
                    assert can_transition(actor, complaint, to_status) is (expected and visible)
                status_events_before = StatusEvent.objects.filter(complaint=complaint).count()
                audit_before = AuditEvent.objects.filter(object_type="Complaint", object_id=str(complaint.pk), action__in=["status_transition", "admin_override"]).count()
                if expected:
                    transition(complaint, to_status, actor=actor, reason=reason, **role_data)
                    successful_roles += 1
                    assert StatusEvent.objects.filter(complaint=complaint).count() == status_events_before + 1
                    assert AuditEvent.objects.filter(object_type="Complaint", object_id=str(complaint.pk), action__in=["status_transition", "admin_override"]).count() == audit_before + 1
                    assert Complaint.objects.get(pk=complaint.pk).status == to_status
                    # Reset only the fixture row to test the next role for the same pair.
                    Complaint.objects.filter(pk=complaint.pk).update(status=from_status)
                else:
                    with pytest.raises(ValidationError):
                        transition(complaint, to_status, actor=actor, reason=reason, **role_data)
                    assert StatusEvent.objects.filter(complaint=complaint).count() == status_events_before
                    assert AuditEvent.objects.filter(object_type="Complaint", object_id=str(complaint.pk), action__in=["status_transition", "admin_override"]).count() == audit_before
            if (from_status, to_status) in TRANSITIONS:
                assert successful_roles == len(TRANSITIONS[(from_status, to_status)])
            else:
                assert successful_roles == 0


@pytest.mark.django_db
def test_transition_helper_scopes_role_actions_to_visible_complaints(workflow_setup):
    citizen_a = workflow_setup["users"][User.Role.CITIZEN]
    citizen_b = User.objects.create_user(email="another@example.test", password="Strong!Password982", name="Another citizen")
    complaint = Complaint.objects.create(
        citizen=citizen_a,
        category=workflow_setup["category"],
        location=Point(0, 0, srid=4326),
        ward=workflow_setup["ward"],
        status=Complaint.Status.SUBMITTED,
        consent_at="2026-01-01T00:00:00Z",
    )
    assert can_transition(citizen_a, complaint, Complaint.Status.CANCELLED)
    assert not can_transition(citizen_b, complaint, Complaint.Status.CANCELLED)
    assert allowed_transition_targets(citizen_b, complaint) == set()


@pytest.mark.django_db
def test_information_request_and_citizen_reply_are_audited_messages(workflow_setup):
    complaint = Complaint.objects.create(
        citizen=workflow_setup["users"][User.Role.CITIZEN],
        category=workflow_setup["category"],
        location=Point(0, 0, srid=4326),
        ward=workflow_setup["ward"],
        status=Complaint.Status.IN_TRIAGE,
        consent_at="2026-01-01T00:00:00Z",
    )
    reviewer = workflow_setup["users"][User.Role.TRIAGE_REVIEWER]
    citizen = workflow_setup["users"][User.Role.CITIZEN]
    transition(complaint, Complaint.Status.INFO_REQUESTED, actor=reviewer, message="Please add a landmark.")
    transition(complaint, Complaint.Status.IN_TRIAGE, actor=citizen, reply="Near the library.")
    assert list(complaint.messages.values_list("body", flat=True)) == ["Please add a landmark.", "Near the library."]
    assert AuditEvent.objects.filter(action="complaint_message_added", object_type="ComplaintMessage").count() == 2


def test_application_status_assignments_stay_inside_transition_service():
    app_root = Path(__file__).resolve().parents[1] / "apps"
    violations = []
    for source in app_root.rglob("*.py"):
        if "migrations" in source.parts or source.name == "services.py" and source.parent.name == "workflow":
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            elif isinstance(node, ast.AugAssign):
                targets = [node.target]
            if any(isinstance(target, ast.Attribute) and target.attr == "status" for target in targets):
                violations.append(f"{source}:{node.lineno}")
    assert violations == []

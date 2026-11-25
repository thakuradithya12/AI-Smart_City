import io
from datetime import date

import pytest
from PIL import Image
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Resolution, StatusEvent
from apps.complaints.services import delete_private_files, private_storage
from apps.workflow.services import add_field_evidence, reassign_complaint, transition
from apps.geography.models import Category, Department, RoutingRule, Ward


def image_file(name="work.jpg"):
    buffer = io.BytesIO()
    Image.new("RGB", (12, 10), "blue").save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.fixture
def day4_setup(db):
    department = Department.objects.create(name="Day Four Roads")
    other_department = Department.objects.create(name="Day Four Water")
    citizen = User.objects.create_user(email="d4-citizen@example.test", password="Strong!Password982", name="Day Four Citizen")
    reviewer = User.objects.create_user(email="d4-reviewer@example.test", password="Strong!Password982", name="Day Four Reviewer", role=User.Role.TRIAGE_REVIEWER)
    official = User.objects.create_user(email="d4-official@example.test", password="Strong!Password982", name="Day Four Official", role=User.Role.DEPARTMENT_OFFICIAL, department=department)
    supervisor = User.objects.create_user(email="d4-supervisor@example.test", password="Strong!Password982", name="Day Four Supervisor", role=User.Role.SUPERVISOR, department=department)
    other_supervisor = User.objects.create_user(email="d4-other-supervisor@example.test", password="Strong!Password982", name="Other Supervisor", role=User.Role.SUPERVISOR, department=other_department)
    admin = User.objects.create_user(email="d4-admin@example.test", password="Strong!Password982", name="Day Four Admin", role=User.Role.ADMIN)
    worker = User.objects.create_user(email="d4-worker@example.test", password="Strong!Password982", name="Day Four Worker", role=User.Role.FIELD_WORKER, department=department)
    other_worker = User.objects.create_user(email="d4-other-worker@example.test", password="Strong!Password982", name="Other Worker", role=User.Role.FIELD_WORKER, department=other_department)
    square = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(name="Day Four Ward", boundary=MultiPolygon(square, srid=4326), source="hand-written test polygon", effective_from=date(2026, 1, 1))
    category = Category.objects.create(name="day-four-test", default_due_hours=24, default_department=department)
    rule = RoutingRule.objects.create(category=category, ward=ward, department=department, version=1, effective_from="2026-01-01T00:00:00Z")
    return locals()


def submit_report(client, setup):
    client.force_login(setup["citizen"])
    response = client.post(reverse("report"), {
        "category": setup["category"].pk, "description": "Street surface is damaged.",
        "latitude": "0", "longitude": "0", "consent": "on", "pin_confirmed": "on",
        "photo": image_file("citizen.jpg"),
    })
    assert response.status_code == 302
    return Complaint.objects.get(citizen=setup["citizen"])


def reach_assigned(client, setup, complaint):
    client.force_login(setup["reviewer"])
    client.post(reverse("route_complaint", args=[complaint.pk]), {})
    complaint.refresh_from_db()
    client.force_login(setup["supervisor"])
    client.post(reverse("acknowledge_complaint", args=[complaint.pk]))
    client.post(reverse("assign_complaint", args=[complaint.pk]), {"assignee": setup["worker"].pk})
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.ASSIGNED


@pytest.mark.django_db
def test_four_user_full_lifecycle_separates_claim_and_verification(client, day4_setup):
    setup = day4_setup
    complaint = submit_report(client, setup)
    reach_assigned(client, setup, complaint)

    client.force_login(setup["worker"])
    client.post(reverse("start_work", args=[complaint.pk]))
    for kind in ("field_before", "field_after"):
        response = client.post(reverse("upload_field_evidence", args=[complaint.pk]), {"kind": kind, "photo": image_file(f"{kind}.jpg")})
        assert response.status_code == 302
    response = client.post(reverse("mark_work_done", args=[complaint.pk]), {"note": "Repaired the damaged road surface."})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.RESOLVED_PENDING_VERIFICATION
    claim = Resolution.objects.get(complaint=complaint)
    assert claim.claimed_by == setup["worker"]
    assert claim.claim_note == "Repaired the damaged road surface."
    assert claim.verified_by is None and claim.verified_at is None

    client.force_login(setup["supervisor"])
    response = client.post(reverse("verify_resolution", args=[complaint.pk]), {"method": "site_review"})
    assert response.status_code == 302
    complaint.refresh_from_db()
    claim.refresh_from_db()
    assert complaint.status == Complaint.Status.VERIFIED_CLOSED
    assert claim.verified_by == setup["supervisor"]
    assert claim.verified_at and claim.outcome == "verified" and claim.method == "site_review"
    assert complaint.status_events.count() == 7
    claim_audit = AuditEvent.objects.get(object_type="Complaint", object_id=str(complaint.pk), after__resolution__claimed_by_id=setup["worker"].pk)
    verify_audit = AuditEvent.objects.get(object_type="Complaint", object_id=str(complaint.pk), after__resolution__outcome="verified")
    assert claim_audit.after["resolution"]["claim_note"] == "Repaired the damaged road surface."
    assert verify_audit.after["resolution"]["verified_by_id"] == setup["supervisor"].pk
    for evidence in complaint.evidence.all():
        delete_private_files((evidence.original_path, evidence.display_path, evidence.thumbnail_path))


@pytest.mark.django_db
def test_dispute_reopens_and_supervisor_reassigns(client, day4_setup):
    setup = day4_setup
    complaint = submit_report(client, setup)
    reach_assigned(client, setup, complaint)
    client.force_login(setup["worker"])
    client.post(reverse("start_work", args=[complaint.pk]))
    client.post(reverse("upload_field_evidence", args=[complaint.pk]), {"kind": "field_after", "photo": image_file()})
    client.post(reverse("mark_work_done", args=[complaint.pk]), {"note": "Work completed at the reported location."})
    client.force_login(setup["citizen"])
    response = client.post(reverse("dispute_resolution", args=[complaint.pk]), {"reason": "The repair is incomplete."})
    assert response.status_code == 302
    complaint.refresh_from_db()
    resolution = complaint.resolution
    assert complaint.status == Complaint.Status.REOPENED
    assert resolution.outcome == "disputed" and resolution.verified_by == setup["citizen"]
    assert complaint.status_events.get(to_status=Complaint.Status.REOPENED).reason == "The repair is incomplete."

    client.force_login(setup["supervisor"])
    response = client.post(reverse("supervisor_reassign", args=[complaint.pk]), {"assignee": setup["worker"].pk})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.ASSIGNED and complaint.assignee == setup["worker"]


@pytest.mark.django_db
def test_citizen_can_cancel_before_acknowledgement(client, day4_setup):
    complaint = submit_report(client, day4_setup)
    client.force_login(day4_setup["citizen"])
    response = client.post(reverse("citizen_cancel", args=[complaint.pk]))
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.CANCELLED
    assert StatusEvent.objects.filter(complaint=complaint, to_status=Complaint.Status.CANCELLED, actor=day4_setup["citizen"]).exists()


@pytest.mark.django_db
def test_worker_cannot_see_unassigned_complaint_or_evidence(client, day4_setup):
    complaint = submit_report(client, day4_setup)
    evidence = complaint.evidence.get()
    client.force_login(day4_setup["worker"])
    assert client.get(reverse("complaint_detail", args=[complaint.pk])).status_code == 404
    assert client.get(reverse("field_task_detail", args=[complaint.pk])).status_code == 404
    assert client.get(reverse("evidence_file", args=[evidence.pk])).status_code == 404
    delete_private_files((evidence.original_path, evidence.display_path, evidence.thumbnail_path))


@pytest.mark.django_db
def test_evidence_display_is_authorized_for_each_role_that_can_see_the_complaint(
    client, day4_setup, monkeypatch
):
    setup = day4_setup
    complaint = Complaint.objects.create(
        public_id="EVIDENCE-ROLE-MATRIX", citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"], department=setup["department"],
        assignee=setup["worker"], status=Complaint.Status.ASSIGNED, consent_at="2026-01-01T00:00:00Z",
    )
    evidence = complaint.evidence.create(
        kind="citizen", original_path="original/private.jpg", display_path="display/private.jpg",
        sha256="c" * 64, uploaded_by=setup["citizen"],
    )
    opened = []
    monkeypatch.setattr(
        "apps.complaints.views.private_storage.open",
        lambda path, mode: (opened.append(path), io.BytesIO(b"display"))[1],
    )
    for actor in (setup["citizen"], setup["reviewer"], setup["official"], setup["supervisor"], setup["worker"], setup["admin"]):
        client.force_login(actor)
        response = client.get(reverse("evidence_file", args=[evidence.pk]))
        assert response.status_code == 200
        response.close()
    assert opened == [evidence.display_path] * 6


@pytest.mark.django_db
def test_other_department_supervisor_cannot_verify_or_reassign(client, day4_setup):
    setup = day4_setup
    complaint = submit_report(client, setup)
    reach_assigned(client, setup, complaint)
    client.force_login(setup["worker"])
    client.post(reverse("start_work", args=[complaint.pk]))
    client.post(reverse("upload_field_evidence", args=[complaint.pk]), {"kind": "field_after", "photo": image_file()})
    client.post(reverse("mark_work_done", args=[complaint.pk]), {"note": "Work completed at the reported location."})
    client.force_login(setup["other_supervisor"])
    assert client.post(reverse("verify_resolution", args=[complaint.pk]), {"method": "site_review"}).status_code == 404
    assert client.post(reverse("supervisor_reassign", args=[complaint.pk]), {"assignee": setup["other_worker"].pk}).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("role", [User.Role.SUPERVISOR, User.Role.DEPARTMENT_OFFICIAL, User.Role.ADMIN])
@pytest.mark.parametrize("status", [Complaint.Status.ASSIGNED, Complaint.Status.IN_PROGRESS])
def test_authorized_staff_can_reassign_without_changing_status(day4_setup, role, status):
    setup = day4_setup
    actor = setup["admin"] if role == User.Role.ADMIN else (
        setup["official"] if role == User.Role.DEPARTMENT_OFFICIAL else setup["supervisor"]
    )
    replacement = User.objects.create_user(
        email=f"replacement-{role}-{status}@example.test", password="Strong!Password982",
        name="Replacement Worker", role=User.Role.FIELD_WORKER, department=setup["department"],
    )
    public_id = f"R-{role[:3]}-{status[:3]}"
    complaint = Complaint.objects.create(
        public_id=public_id, citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"], department=setup["department"],
        assignee=setup["worker"], status=status, consent_at="2026-01-01T00:00:00Z",
    )
    before_events = complaint.status_events.count()
    reassign_complaint(complaint, actor, replacement, "Worker unavailable for this task")
    complaint.refresh_from_db()
    assert complaint.status == status
    assert complaint.assignee == replacement
    assert complaint.status_events.count() == before_events
    audit = AuditEvent.objects.get(
        action="admin_override" if role == User.Role.ADMIN else "complaint_reassigned",
        object_id=str(complaint.pk),
    )
    assert audit.before == {"assignee_id": setup["worker"].pk}
    assert audit.after == {"assignee_id": replacement.pk}
    assert audit.reason == "Worker unavailable for this task"


@pytest.mark.django_db
def test_reassignment_rejects_invalid_actor_reason_worker_and_terminal_status(day4_setup):
    setup = day4_setup
    replacement = User.objects.create_user(
        email="inactive-replacement@example.test", password="Strong!Password982", name="Inactive",
        role=User.Role.FIELD_WORKER, department=setup["department"], is_active=False,
    )
    wrong_department_worker = setup["other_worker"]
    complaint = Complaint.objects.create(
        public_id="REASSIGN-INVALID", citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"], department=setup["department"],
        assignee=setup["worker"], status=Complaint.Status.ASSIGNED, consent_at="2026-01-01T00:00:00Z",
    )
    for worker, reason in ((replacement, "valid reason"), (wrong_department_worker, "valid reason"),
                           (setup["worker"], "no")):
        with pytest.raises(ValidationError):
            reassign_complaint(complaint, setup["supervisor"], worker, reason)
    with pytest.raises(ValidationError):
        reassign_complaint(complaint, setup["reviewer"], setup["worker"], "valid reason")
    complaint.status = Complaint.Status.VERIFIED_CLOSED
    complaint.save(update_fields=["status"])
    with pytest.raises(ValidationError):
        reassign_complaint(complaint, setup["supervisor"], setup["worker"], "valid reason")


@pytest.mark.django_db
def test_reassignment_endpoint_hides_task_and_evidence_from_previous_worker(client, day4_setup):
    setup = day4_setup
    replacement = User.objects.create_user(
        email="new-worker@example.test", password="Strong!Password982", name="New Worker",
        role=User.Role.FIELD_WORKER, department=setup["department"],
    )
    complaint = Complaint.objects.create(
        public_id="REASSIGN-VISIBILITY", citizen=setup["citizen"], category=setup["category"],
        location=Point(0, 0, srid=4326), ward=setup["ward"], department=setup["department"],
        assignee=setup["worker"], status=Complaint.Status.IN_PROGRESS, consent_at="2026-01-01T00:00:00Z",
    )
    evidence = complaint.evidence.create(kind="field_before", original_path="private/original.jpg",
        display_path="private/display.jpg", sha256="a" * 64, uploaded_by=setup["worker"])
    client.force_login(setup["official"])
    response = client.post(reverse("supervisor_reassign", args=[complaint.pk]), {
        "assignee": replacement.pk, "reason": "Worker unavailable for this task",
    })
    assert response.status_code == 302
    client.force_login(setup["worker"])
    assert client.get(reverse("field_task_detail", args=[complaint.pk])).status_code == 404
    assert client.get(reverse("evidence_file", args=[evidence.pk])).status_code == 404
    client.force_login(setup["citizen"])
    detail = client.get(reverse("complaint_detail", args=[complaint.pk]))
    assert b"Work assignment updated" in detail.content
    assert b"New Worker" not in detail.content


@pytest.mark.django_db
def test_marking_done_without_after_photo_is_refused(client, day4_setup):
    setup = day4_setup
    complaint = submit_report(client, setup)
    reach_assigned(client, setup, complaint)
    client.force_login(setup["worker"])
    client.post(reverse("start_work", args=[complaint.pk]))
    response = client.post(reverse("mark_work_done", args=[complaint.pk]), {"note": "Work completed at the reported location."})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_PROGRESS
    assert not Resolution.objects.filter(complaint=complaint).exists()


@pytest.mark.django_db
def test_department_official_cannot_mark_work_done_by_post_or_transition(client, day4_setup):
    setup = day4_setup
    complaint = submit_report(client, setup)
    reach_assigned(client, setup, complaint)
    client.force_login(setup["worker"])
    client.post(reverse("start_work", args=[complaint.pk]))
    client.post(reverse("upload_field_evidence", args=[complaint.pk]), {"kind": "field_after", "photo": image_file("after.jpg")})

    client.force_login(setup["official"])
    response = client.post(reverse("mark_work_done", args=[complaint.pk]), {"note": "Completed work on the report."})
    assert response.status_code == 404
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_PROGRESS
    with pytest.raises(ValidationError):
        transition(complaint, Complaint.Status.RESOLVED_PENDING_VERIFICATION, actor=setup["official"], note="Completed work on the report.")


@pytest.mark.django_db
def test_field_evidence_service_rechecks_locked_status_before_storing(day4_setup):
    setup = day4_setup
    complaint = Complaint.objects.create(
        public_id="D4-LOCKED-EVIDENCE",
        citizen=setup["citizen"],
        category=setup["category"],
        location=Point(0, 0, srid=4326),
        ward=setup["ward"],
        department=setup["department"],
        assignee=setup["worker"],
        status=Complaint.Status.IN_PROGRESS,
        consent_at="2026-01-01T00:00:00Z",
    )
    stale_instance = Complaint.objects.get(pk=complaint.pk)
    Complaint.objects.filter(pk=complaint.pk).update(status=Complaint.Status.RESOLVED_PENDING_VERIFICATION)

    with pytest.raises(ValidationError, match="only be added while work is in progress"):
        add_field_evidence(stale_instance, setup["worker"], image_file(), "field_after")

    assert not complaint.evidence.exists()


@pytest.mark.django_db
def test_field_evidence_and_private_files_roll_back_when_audit_write_fails(day4_setup, monkeypatch):
    setup = day4_setup
    complaint = Complaint.objects.create(
        public_id="D4-AUDIT-FAIL-EVIDENCE",
        citizen=setup["citizen"],
        category=setup["category"],
        location=Point(0, 0, srid=4326),
        ward=setup["ward"],
        department=setup["department"],
        assignee=setup["worker"],
        status=Complaint.Status.IN_PROGRESS,
        consent_at="2026-01-01T00:00:00Z",
    )

    def stored_names(directory):
        try:
            return set(private_storage.listdir(directory)[1])
        except FileNotFoundError:
            return set()

    originals_before = stored_names("original")
    displays_before = stored_names("display")
    thumbnails_before = stored_names("thumbnail")
    original_save = AuditEvent.save

    def fail_evidence_audit(self, *args, **kwargs):
        if self.action == "evidence_uploaded":
            raise RuntimeError("injected evidence audit failure")
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(AuditEvent, "save", fail_evidence_audit)
    with pytest.raises(RuntimeError, match="injected evidence audit failure"):
        add_field_evidence(complaint, setup["worker"], image_file(), "field_after")

    assert not complaint.evidence.exists()
    assert stored_names("original") == originals_before
    assert stored_names("display") == displays_before
    assert stored_names("thumbnail") == thumbnails_before


@pytest.mark.django_db
def test_deactivated_users_are_not_authorized_to_view_complaints(day4_setup):
    complaint = Complaint.objects.create(
        public_id="D4-INACTIVE-USER",
        citizen=day4_setup["citizen"],
        category=day4_setup["category"],
        location=Point(0, 0, srid=4326),
        ward=day4_setup["ward"],
        status=Complaint.Status.IN_TRIAGE,
        consent_at="2026-01-01T00:00:00Z",
    )
    inactive_reviewer = User.objects.create_user(
        email="inactive-reviewer@example.test",
        password="Strong!Password982",
        name="Inactive reviewer",
        role=User.Role.TRIAGE_REVIEWER,
        is_active=False,
    )
    assert not Complaint.objects.visible_to(inactive_reviewer).filter(pk=complaint.pk).exists()


@pytest.mark.django_db
def test_information_request_reply_cancel_and_timeline_are_exposed(client, day4_setup):
    setup = day4_setup
    complaint = submit_report(client, setup)
    client.force_login(setup["reviewer"])
    client.post(reverse("request_information", args=[complaint.pk]), {"message": "Please add a nearby landmark."})
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.INFO_REQUESTED
    client.force_login(setup["citizen"])
    response = client.post(reverse("citizen_reply", args=[complaint.pk]), {"message": "It is beside the public library."})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_TRIAGE
    assert complaint.messages.count() == 2
    response = client.get(reverse("complaint_detail", args=[complaint.pk]))
    assert b"Evidence: Citizen" in response.content


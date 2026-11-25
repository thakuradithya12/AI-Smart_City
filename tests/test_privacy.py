import json
from datetime import timedelta
from io import StringIO

import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import PrivacyDeletionRequest, User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Evidence, StatusEvent
from apps.geography.models import Category
from apps.accounts.management.commands import purge_expired


@pytest.fixture
def privacy_citizen(db):
    return User.objects.create_user(
        phone_number="9876543210", password="Strong!Password982", name="Privacy Citizen"
    )


@pytest.mark.django_db
def test_privacy_notice_is_public_and_export_includes_phone_and_only_visible_complaints(
    client, privacy_citizen,
):
    category = Category.objects.create(name="privacy-test")
    own = Complaint.objects.create(
        public_id="PRIVACY-OWN", citizen=privacy_citizen, category=category,
        location=Point(78.48, 17.38, srid=4326), consent_at=timezone.now(),
        consent_version="2026-11-25-v1",
    )
    other_user = User.objects.create_user(
        phone_number="9876543211", password="Strong!Password982", name="Other Citizen"
    )
    Complaint.objects.create(
        public_id="PRIVACY-OTHER", citizen=other_user, category=category,
        location=Point(78.48, 17.38, srid=4326), consent_at=timezone.now(),
    )

    notice = client.get(reverse("privacy_notice"))
    assert notice.status_code == 200
    assert b"Retention" in notice.content
    client.force_login(privacy_citizen)
    response = client.get(reverse("privacy_export"))

    data = json.loads(response.content)
    assert response["Cache-Control"] == "private, no-store"
    assert data["account"]["phone_number"] == "+919876543210"
    assert [row["public_id"] for row in data["complaints"]] == [own.public_id]
    assert data["complaints"][0]["consent_version"] == "2026-11-25-v1"


@pytest.mark.django_db
def test_citizen_deletion_request_is_idempotent_and_keeps_anonymised_audit_actor(client, privacy_citizen):
    client.force_login(privacy_citizen)
    first = client.post(reverse("privacy_delete_request"))
    second = client.post(reverse("privacy_delete_request"))
    assert first.status_code == second.status_code == 302
    assert PrivacyDeletionRequest.objects.filter(user=privacy_citizen, processed_at__isnull=True).count() == 1

    call_command("purge_expired", stdout=StringIO())
    privacy_citizen.refresh_from_db()
    deletion_request = PrivacyDeletionRequest.objects.get(user=privacy_citizen)
    event = AuditEvent.objects.get(action="privacy_deletion_processed", object_id=str(privacy_citizen.pk))
    assert deletion_request.processed_at is not None
    assert privacy_citizen.name == "Deleted user"
    assert privacy_citizen.phone_number is None and privacy_citizen.email is None
    assert privacy_citizen.is_active is False
    assert event.actor_id == privacy_citizen.pk
    assert event.actor.name == "Deleted user"


@pytest.mark.django_db(transaction=True)
def test_retention_purge_removes_expired_details_and_files_but_keeps_append_only_history(
    privacy_citizen, monkeypatch,
):
    category = Category.objects.create(name="retention-test")
    complaint = Complaint.objects.create(
        public_id="RETENTION-OLD", citizen=privacy_citizen, category=category,
        status=Complaint.Status.VERIFIED_CLOSED,
        location=Point(78.48, 17.38, srid=4326), description="Details to expire",
        landmark="Private landmark", consent_at=timezone.now(), due_at=timezone.now(),
    )
    event = StatusEvent.objects.create(
        complaint=complaint, from_status=Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        to_status=Complaint.Status.VERIFIED_CLOSED, actor=privacy_citizen, role="citizen",
        created_at=timezone.now() - timedelta(days=366),
    )
    evidence = Evidence.objects.create(
        complaint=complaint, kind=Evidence.Kind.CITIZEN,
        original_path="original/expired.jpg", display_path="display/expired.jpg",
        thumbnail_path="thumbnail/expired.jpg", sha256="1" * 64, uploaded_by=privacy_citizen,
    )
    deleted_paths = []
    monkeypatch.setattr(purge_expired, "delete_private_files", lambda paths: deleted_paths.extend(paths))

    call_command("purge_expired", stdout=StringIO())

    complaint.refresh_from_db()
    assert complaint.location is None
    assert complaint.description == complaint.landmark == ""
    assert complaint.retention_purged_at is not None
    assert not Evidence.objects.filter(pk=evidence.pk).exists()
    assert StatusEvent.objects.filter(pk=event.pk).exists()
    assert set(deleted_paths) == {
        "original/expired.jpg", "display/expired.jpg", "thumbnail/expired.jpg"
    }


@pytest.mark.django_db
def test_overlapping_retention_command_exits_when_advisory_lock_is_held(privacy_citizen, monkeypatch):
    request = PrivacyDeletionRequest.objects.create(user=privacy_citizen)
    monkeypatch.setattr(purge_expired.Command, "_try_lock", lambda _self: False)
    output = StringIO()

    call_command("purge_expired", stdout=output)

    assert "Another purge_expired run holds the lock" in output.getvalue()
    assert PrivacyDeletionRequest.objects.get(pk=request.pk).processed_at is None
    privacy_citizen.refresh_from_db()
    assert privacy_citizen.phone_number == "+919876543210"


@pytest.mark.django_db
def test_inactive_accounts_are_anonymised_after_24_months_only():
    old_inactive = User.objects.create_user(
        phone_number="9876543212", password="Strong!Password982", name="Old inactive"
    )
    recent_inactive = User.objects.create_user(
        phone_number="9876543213", password="Strong!Password982", name="Recent inactive"
    )
    cutoff = timezone.now() - timedelta(days=730)
    User.objects.filter(pk=old_inactive.pk).update(is_active=False, date_joined=cutoff - timedelta(days=1))
    User.objects.filter(pk=recent_inactive.pk).update(is_active=False)

    call_command("purge_expired", stdout=StringIO())

    old_inactive.refresh_from_db()
    recent_inactive.refresh_from_db()
    assert old_inactive.phone_number is None and old_inactive.name == "Deleted user"
    assert recent_inactive.phone_number == "+919876543213"

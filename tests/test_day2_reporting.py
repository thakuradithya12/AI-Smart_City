import hashlib
import io
from io import StringIO

import pytest
from PIL import Image
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Evidence, StatusEvent
from apps.complaints.services import delete_private_files, private_storage, store_citizen_image
from apps.geography.models import Category, Ward
from apps.geography.models import RoutingRule


def make_image(*, format="JPEG", size=(12, 10), exif=None):
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format=format, exif=exif or b"")
    return buffer.getvalue()


@pytest.fixture
def citizen(db):
    return User.objects.create_user(email="citizen2@example.test", password="Strong!Password123", name="Citizen Two")


@pytest.fixture
def ward(db):
    square = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    return Ward.objects.create(name="Test Ward", boundary=MultiPolygon(square, srid=4326), source="hand-written test polygon", effective_from="2026-01-01")


@pytest.fixture
def category(db):
    return Category.objects.create(name="pothole", default_due_hours=24)


@pytest.mark.django_db
@pytest.mark.parametrize("payload,content_type", [(b"not image", "text/plain"), (b"x" * (8 * 1024 * 1024 + 1), "image/jpeg")])
def test_bad_or_oversized_image_rejected(payload, content_type):
    with pytest.raises(ValidationError):
        store_citizen_image(SimpleUploadedFile("bad", payload, content_type=content_type))


@pytest.mark.django_db
def test_corrupt_image_rejected():
    with pytest.raises(ValidationError):
        store_citizen_image(SimpleUploadedFile("broken.jpg", b"\xff\xd8broken", content_type="image/jpeg"))


@pytest.mark.django_db
def test_original_hash_and_exif_free_display():
    exif = Image.Exif()
    exif[270] = "private caption"
    raw = make_image(exif=exif)
    original, display, digest = store_citizen_image(SimpleUploadedFile("photo.jpg", raw, content_type="image/jpeg"))
    assert private_storage.open(original, "rb").read() == raw
    assert digest == hashlib.sha256(raw).hexdigest()
    with Image.open(private_storage.open(display, "rb")) as image:
        assert not image.getexif()
    delete_private_files((original, display))


@pytest.mark.django_db
def test_registration_weak_password_rejected(client):
    response = client.post(reverse("register"), {"email": "weak@example.test", "name": "Weak User", "password1": "123", "password2": "123"})
    assert response.status_code == 200
    assert not User.objects.filter(email="weak@example.test").exists()


@pytest.mark.django_db
def test_registration_and_login(client):
    response = client.post(reverse("register"), {"email": "new@example.test", "name": "New Citizen", "password1": "Good!Password982", "password2": "Good!Password982"})
    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    user = User.objects.get(email="new@example.test")
    assert user.role == User.Role.CITIZEN
    client.logout()
    response = client.post(reverse("login"), {"username": user.email, "password": "Good!Password982"})
    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    assert str(user.pk) == client.session.get("_auth_user_id")


@pytest.mark.django_db
def test_authenticated_user_visiting_login_is_sent_to_workspace(client, citizen):
    client.force_login(citizen)

    response = client.get(reverse("login"))

    assert response.status_code == 302
    assert response.url == reverse("dashboard")


@pytest.mark.django_db
def test_seed_demo_creates_coordinate_ward_defaults_and_prints_passwords_once():
    output = StringIO()
    with override_settings(DEBUG=True):
        call_command("seed_demo", lat=12.3456, lon=78.9012, stdout=output)
    ward = Ward.objects.get(name="Demo Ward")
    assert ward.boundary.covers(Point(78.9012, 12.3456, srid=4326))
    assert ward.source.startswith("hand-drawn, ")
    assert set(Category.objects.values_list("name", flat=True)) == {"pothole", "garbage", "drainage", "streetlight", "water_leakage", "other"}
    assert User.objects.count() == 5
    assert RoutingRule.objects.filter(ward=ward).count() == 6
    demo_department = User.objects.get(role=User.Role.FIELD_WORKER).department
    assert set(Category.objects.values_list("default_department_id", flat=True)) == {demo_department.pk}
    assert set(RoutingRule.objects.filter(ward=ward).values_list("department_id", flat=True)) == {demo_department.pk}
    assert output.getvalue().count("@example.test ") == 5

    second_output = StringIO()
    with override_settings(DEBUG=True):
        call_command("seed_demo", lat=12.3456, lon=78.9012, stdout=second_output)
    assert "Skipped existing account" in second_output.getvalue()
    assert "@example.test " not in second_output.getvalue()


@pytest.mark.django_db
def test_seed_demo_requires_force_when_debug_is_false():
    with override_settings(DEBUG=False):
        with pytest.raises(CommandError, match="Pass --force"):
            call_command("seed_demo", lat=12, lon=78)
        call_command("seed_demo", lat=12, lon=78, force=True, stdout=StringIO())


@pytest.mark.django_db
def test_report_creates_complaint_evidence_and_events(client, citizen, ward, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {"category": category.pk, "description": "Pothole", "latitude": "0", "longitude": "0", "gps_accuracy_m": "4.75", "consent": "on", "pin_confirmed": "on", "photo": SimpleUploadedFile("test.jpg", make_image(), content_type="image/jpeg")})
    assert response.status_code == 302
    complaint = Complaint.objects.get(citizen=citizen)
    assert complaint.status == Complaint.Status.IN_TRIAGE
    assert complaint.public_id.endswith(f"{complaint.pk:06d}")
    assert complaint.ward == ward and complaint.due_at
    assert str(complaint.gps_accuracy_m) == "4.75"
    assert complaint.evidence.count() == 1
    assert complaint.status_events.count() == 1
    assert AuditEvent.objects.filter(object_id=str(complaint.pk)).count() == 2
    evidence = complaint.evidence.get()
    delete_private_files((evidence.original_path, evidence.display_path))


@pytest.mark.django_db
@override_settings(REPORT_POST_LIMIT=1, REPORT_POST_WINDOW_SECONDS=3600)
def test_report_post_limit_is_enforced_for_authenticated_citizen(client, citizen):
    cache.clear()
    client.force_login(citizen)
    assert client.get(reverse("report")).status_code == 200
    assert client.post(reverse("report"), {}).status_code == 200
    limited = client.post(reverse("report"), {})
    assert limited.status_code == 429
    assert "Report limit reached" in limited.content.decode()
    cache.clear()


@pytest.mark.django_db
def test_outside_ward_fails_without_complaint(client, citizen, ward, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {"category": category.pk, "latitude": "4", "longitude": "4", "consent": "on", "pin_confirmed": "on", "photo": SimpleUploadedFile("test.jpg", make_image(), content_type="image/jpeg")})
    assert response.status_code == 200
    assert "outside the supported area" in response.content.decode()
    assert not Complaint.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("effective_from,effective_to", [("2027-01-01", None), ("2020-01-01", "2020-12-31")])
def test_report_rejects_pin_in_ward_outside_effective_dates(client, citizen, category, effective_from, effective_to):
    polygon = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    Ward.objects.create(
        name="Inactive Test Ward",
        boundary=MultiPolygon(polygon, srid=4326),
        source="test-only polygon with inactive effective dates",
        effective_from=effective_from,
        effective_to=effective_to,
    )
    client.force_login(citizen)
    response = client.post(reverse("report"), {
        "category": category.pk,
        "latitude": "0",
        "longitude": "0",
        "consent": "on",
        "pin_confirmed": "on",
        "photo": SimpleUploadedFile("inactive-ward.jpg", make_image(), content_type="image/jpeg"),
    })
    assert response.status_code == 200
    assert "outside the supported area" in response.content.decode()
    assert not Complaint.objects.exists()


@pytest.mark.django_db
def test_ward_effective_end_cannot_precede_start_in_model_or_database():
    polygon = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward(
        name="Invalid Effective Window",
        boundary=MultiPolygon(polygon, srid=4326),
        source="test-only polygon",
        effective_from="2026-12-01",
        effective_to="2026-11-30",
    )
    with pytest.raises(ValidationError, match="on or after the start date"):
        ward.full_clean()

    # Bulk writes can skip model validation; the database constraint still rejects invalid ranges.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ward.save(force_insert=True)


@pytest.mark.django_db
def test_pin_confirmation_is_required_on_server(client, citizen, ward, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {"category": category.pk, "latitude": "0", "longitude": "0", "consent": "on", "photo": SimpleUploadedFile("test.jpg", make_image(), content_type="image/jpeg")})
    assert response.status_code == 200
    assert not Complaint.objects.exists()


@pytest.mark.django_db
def test_creation_atomic_when_transition_fails(client, citizen, ward, category, monkeypatch):
    client.force_login(citizen)
    from apps.complaints import views

    def fail_transition(*args, **kwargs):
        raise RuntimeError("injected transition failure")

    monkeypatch.setattr(views, "transition", fail_transition)
    with pytest.raises(RuntimeError):
        client.post(reverse("report"), {"category": category.pk, "latitude": "0", "longitude": "0", "consent": "on", "pin_confirmed": "on", "photo": SimpleUploadedFile("test.jpg", make_image(), content_type="image/jpeg")})
    assert not Complaint.objects.exists()
    assert not Evidence.objects.exists()


@pytest.mark.django_db
def test_validation_failure_after_storage_removes_private_files(client, citizen, ward, category, monkeypatch):
    client.force_login(citizen)
    from apps.complaints import views

    def reject_transition(*args, **kwargs):
        raise ValidationError("injected validation failure")

    monkeypatch.setattr(views, "transition", reject_transition)
    try:
        original_before = set(private_storage.listdir("original")[1])
    except FileNotFoundError:
        original_before = set()
    try:
        display_before = set(private_storage.listdir("display")[1])
    except FileNotFoundError:
        display_before = set()
    response = client.post(reverse("report"), {"category": category.pk, "latitude": "0", "longitude": "0", "consent": "on", "pin_confirmed": "on", "photo": SimpleUploadedFile("test.jpg", make_image(), content_type="image/jpeg")})
    assert response.status_code == 200
    assert not Complaint.objects.exists()
    assert not Evidence.objects.exists()
    assert set(private_storage.listdir("original")[1]) == original_before
    assert set(private_storage.listdir("display")[1]) == display_before


@pytest.mark.django_db
def test_other_citizen_cannot_view_detail_or_photo(client, citizen, ward, category):
    image = make_image()
    client.force_login(citizen)
    client.post(reverse("report"), {"category": category.pk, "latitude": "0", "longitude": "0", "consent": "on", "pin_confirmed": "on", "photo": SimpleUploadedFile("test.jpg", image, content_type="image/jpeg")})
    complaint = Complaint.objects.get()
    evidence = Evidence.objects.get()
    stranger = User.objects.create_user(email="stranger@example.test", password="Strong!Password123", name="Stranger")
    client.force_login(stranger)
    assert client.get(reverse("complaint_detail", args=[complaint.pk])).status_code == 404
    assert client.get(reverse("evidence_file", args=[evidence.pk])).status_code == 404
    delete_private_files((evidence.original_path, evidence.display_path))


@pytest.mark.django_db
def test_status_and_audit_events_are_append_only(citizen, ward, category):
    complaint = Complaint.objects.create(citizen=citizen, category=category, location=Point(0, 0, srid=4326), consent_at="2026-01-01T00:00:00Z", ward=ward)
    status = StatusEvent.objects.create(complaint=complaint, from_status="submitted", to_status="in_triage", role="system")
    audit = AuditEvent.objects.create(role="system", action="test", object_type="Complaint", object_id=str(complaint.pk))
    for event in (status, audit):
        with pytest.raises(ValueError):
            event.save()
        with pytest.raises(ValueError):
            event.delete()
    with pytest.raises(ValueError, match="Status events are append-only"):
        StatusEvent.objects.filter(pk=status.pk).update(reason="rewritten")
    with pytest.raises(ValueError, match="Status events are append-only"):
        StatusEvent.objects.filter(pk=status.pk).delete()
    with pytest.raises(ValueError, match="Audit events are append-only"):
        AuditEvent.objects.filter(pk=audit.pk).update(reason="rewritten")
    with pytest.raises(ValueError, match="Audit events are append-only"):
        AuditEvent.objects.filter(pk=audit.pk).delete()

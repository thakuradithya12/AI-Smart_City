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
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.management.commands.seed_demo import DEMO_LATITUDE, DEMO_LONGITUDE
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Evidence, StatusEvent
from apps.complaints.forms import ReportForm
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
def test_image_pixel_limit_rejected(monkeypatch):
    monkeypatch.setattr("apps.complaints.services.MAX_IMAGE_PIXELS", 100)
    with pytest.raises(ValidationError, match="dimensions are too large"):
        store_citizen_image(SimpleUploadedFile("large.jpg", make_image(size=(12, 10)), content_type="image/jpeg"))


@pytest.mark.django_db
def test_original_hash_and_exif_free_display():
    exif = Image.Exif()
    exif[270] = "private caption"
    raw = make_image(exif=exif)
    original, display, thumbnail, digest = store_citizen_image(SimpleUploadedFile("photo.jpg", raw, content_type="image/jpeg"))
    assert private_storage.open(original, "rb").read() == raw
    assert digest == hashlib.sha256(raw).hexdigest()
    with Image.open(private_storage.open(display, "rb")) as image:
        assert not image.getexif()
        assert max(image.size) <= 1600
    with Image.open(private_storage.open(thumbnail, "rb")) as image:
        assert not image.getexif()
        assert max(image.size) <= 320
    delete_private_files((original, display, thumbnail))


@pytest.mark.django_db
def test_display_copy_uses_configured_max_edge(settings):
    settings.EVIDENCE_DISPLAY_MAX_EDGE = 8
    raw = make_image(size=(30, 20))
    original, display, thumbnail, _digest = store_citizen_image(
        SimpleUploadedFile("large.jpg", raw, content_type="image/jpeg")
    )
    with Image.open(private_storage.open(display, "rb")) as image:
        assert image.size == (8, 5)
    delete_private_files((original, display, thumbnail))


@pytest.mark.django_db
@override_settings(REPORT_MAX_PHOTOS=2)
def test_report_accepts_multiple_citizen_photos(client, citizen, ward, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {
        "category": category.pk, "latitude": "0", "longitude": "0", "consent": "on",
        "pin_confirmed": "on", "photo": [
            SimpleUploadedFile("first.jpg", make_image(), content_type="image/jpeg"),
            SimpleUploadedFile("second.jpg", make_image(format="PNG"), content_type="image/png"),
        ],
    })
    assert response.status_code == 302
    evidence = list(Complaint.objects.get().evidence.filter(kind=Evidence.Kind.CITIZEN))
    assert len(evidence) == 2
    delete_private_files(path for item in evidence for path in (item.original_path, item.display_path, item.thumbnail_path))


@pytest.mark.django_db
@override_settings(REPORT_MAX_PHOTOS=1)
def test_report_rejects_more_than_configured_citizen_photo_limit(client, citizen, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {
        "category": category.pk, "latitude": "0", "longitude": "0", "consent": "on",
        "pin_confirmed": "on", "photo": [
            SimpleUploadedFile("first.jpg", make_image(), content_type="image/jpeg"),
            SimpleUploadedFile("second.jpg", make_image(), content_type="image/jpeg"),
        ],
    })
    assert response.status_code == 200
    assert not Complaint.objects.exists()


@pytest.mark.django_db
def test_media_reconcile_reports_orphan_without_deleting_it():
    orphan = private_storage.save("display/reconcile-orphan.jpg", ContentFile(b"kept"))
    output = StringIO()
    call_command("media_reconcile", stdout=output)
    assert orphan in output.getvalue()
    assert private_storage.exists(orphan)
    private_storage.delete(orphan)


@pytest.mark.django_db
def test_registration_weak_password_rejected(client):
    response = client.post(reverse("register"), {"phone_number": "9876543210", "name": "Weak User", "password1": "123", "password2": "123"})
    assert response.status_code == 200
    assert not User.objects.filter(phone_number="+919876543210").exists()


@pytest.mark.django_db
def test_report_photo_input_has_mobile_file_hints(client, citizen):
    client.force_login(citizen)

    response = client.get(reverse("report"))

    assert response.status_code == 200
    assert b'accept="image/jpeg,image/png,image/webp"' in response.content
    assert b'capture="environment"' in response.content


@pytest.mark.django_db
def test_report_page_has_guided_flow_controls_and_photo_preview(client, citizen):
    client.force_login(citizen)

    response = client.get(reverse("report"))

    assert response.status_code == 200
    assert b"report-flow.js" in response.content
    assert b"photo-preview" in response.content
    assert b"report-review" in response.content
    assert b"Nearby landmark or address" in response.content
    assert b"not an emergency service" in response.content


@pytest.mark.django_db
def test_report_saves_optional_landmark(client, citizen, ward, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {
        "category": category.pk,
        "description": "Broken road surface",
        "landmark": "Near the public library",
        "latitude": "0",
        "longitude": "0",
        "consent": "on",
        "pin_confirmed": "on",
        "photo": SimpleUploadedFile("landmark.jpg", make_image(), content_type="image/jpeg"),
    })

    assert response.status_code == 302
    complaint = Complaint.objects.get(citizen=citizen)
    assert complaint.landmark == "Near the public library"
    evidence = complaint.evidence.get()
    delete_private_files((evidence.original_path, evidence.display_path, evidence.thumbnail_path))


@pytest.mark.django_db
def test_report_rejects_landmark_over_limit(client, citizen, ward, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {
        "category": category.pk,
        "landmark": "x" * 161,
        "latitude": "0",
        "longitude": "0",
        "consent": "on",
        "pin_confirmed": "on",
        "photo": SimpleUploadedFile("landmark.jpg", make_image(), content_type="image/jpeg"),
    })

    assert response.status_code == 200
    assert "Ensure this value has at most 160 characters" in response.content.decode()
    assert not Complaint.objects.exists()


@pytest.mark.django_db
def test_report_validation_error_preserves_text_and_location(client, citizen, category):
    client.force_login(citizen)
    response = client.post(reverse("report"), {
        "category": category.pk,
        "description": "Broken drain cover",
        "landmark": "Near the bus stop",
        "latitude": "4",
        "longitude": "4",
        "consent": "on",
        "pin_confirmed": "on",
        "photo": SimpleUploadedFile("outside.jpg", make_image(), content_type="image/jpeg"),
    })

    assert response.status_code == 200
    assert b'value="4"' in response.content
    assert b"Broken drain cover" in response.content
    assert b"Near the bus stop" in response.content
    assert not Complaint.objects.exists()


@pytest.mark.django_db
def test_report_category_choices_exclude_inactive_categories(category):
    inactive = Category.objects.create(name="retired-category", is_active=False)
    form = ReportForm()
    assert category.pk in form.fields["category"].queryset.values_list("pk", flat=True)
    assert inactive.pk not in form.fields["category"].queryset.values_list("pk", flat=True)


@pytest.mark.django_db
def test_evidence_response_has_private_safe_headers_and_never_opens_original(
    client, citizen, ward, category, monkeypatch
):
    complaint = Complaint.objects.create(
        citizen=citizen,
        category=category,
        location=Point(0, 0, srid=4326),
        ward=ward,
        consent_at="2026-01-01T00:00:00Z",
    )
    evidence = Evidence.objects.create(
        complaint=complaint,
        kind=Evidence.Kind.CITIZEN,
        original_path="original/private.jpg",
        display_path="display/photo.jpg",
        sha256="a" * 64,
        uploaded_by=citizen,
    )
    opened = []

    def open_display(path, mode):
        opened.append(path)
        return io.BytesIO(b"display image bytes")

    monkeypatch.setattr("apps.complaints.views.private_storage.open", open_display)
    client.force_login(citizen)

    response = client.get(reverse("evidence_file", args=[evidence.pk]))

    assert response.status_code == 200
    assert response["Cache-Control"] == "private, max-age=300"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Content-Disposition"] == "inline"
    assert opened == [evidence.display_path]


@pytest.mark.django_db
def test_deactivated_account_cannot_fetch_evidence(client, citizen, ward, category, monkeypatch):
    complaint = Complaint.objects.create(
        citizen=citizen, category=category, location=Point(0, 0, srid=4326), ward=ward,
        consent_at="2026-01-01T00:00:00Z",
    )
    evidence = Evidence.objects.create(
        complaint=complaint, kind=Evidence.Kind.CITIZEN, original_path="original/secret.jpg",
        display_path="display/secret.jpg", sha256="b" * 64, uploaded_by=citizen,
    )
    inactive = User.objects.create_user(
        email="inactive-evidence@example.test", password="Strong!Password123", name="Inactive",
        is_active=False,
    )
    opened = []
    monkeypatch.setattr("apps.complaints.views.private_storage.open", lambda *args: opened.append(args))
    client.force_login(inactive)
    response = client.get(reverse("evidence_file", args=[evidence.pk]))
    assert response.status_code != 200
    assert opened == []


@pytest.mark.django_db
def test_registration_and_login(client):
    response = client.post(reverse("register"), {"phone_number": "98765 43210", "name": "New Citizen", "password1": "Good!Password982", "password2": "Good!Password982"})
    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    user = User.objects.get(phone_number="+919876543210")
    assert user.email is None
    assert user.username == user.phone_number
    assert user.role == User.Role.CITIZEN
    client.logout()
    response = client.post(reverse("login"), {"username": "+91 (98765) 43210", "password": "Good!Password982"})
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
def test_seed_demo_creates_hyderabad_demo_ward_defaults_and_prints_passwords_once():
    output = StringIO()
    with override_settings(DEBUG=True):
        call_command("seed_demo", stdout=output)
    ward = Ward.objects.get(name="Demo Ward")
    assert ward.boundary.covers(Point(DEMO_LONGITUDE, DEMO_LATITUDE, srid=4326))
    assert "Hyderabad, Telangana" in ward.source
    assert "not pilot data" in ward.source
    assert ward.boundary.covers(Point(DEMO_LONGITUDE + 0.05, DEMO_LATITUDE + 0.05, srid=4326))
    assert not ward.boundary.covers(Point(77.5946, 12.9716, srid=4326))
    assert set(Category.objects.values_list("name", flat=True)) == {"pothole", "garbage", "drainage", "streetlight", "water_leakage", "other"}
    assert dict(Category.objects.values_list("name", "label")) == {
        "pothole": "Pothole", "garbage": "Garbage", "drainage": "Drainage",
        "streetlight": "Streetlight", "water_leakage": "Water leakage", "other": "Other",
    }
    assert User.objects.count() == 5
    assert RoutingRule.objects.filter(ward=ward).count() == 6
    demo_department = User.objects.get(role=User.Role.FIELD_WORKER).department
    assert set(Category.objects.values_list("default_department_id", flat=True)) == {demo_department.pk}
    assert set(RoutingRule.objects.filter(ward=ward).values_list("department_id", flat=True)) == {demo_department.pk}
    assert output.getvalue().count("@example.test ") == 5

    second_output = StringIO()
    with override_settings(DEBUG=True):
        call_command("seed_demo", stdout=second_output)
    assert "Skipped existing account" in second_output.getvalue()
    assert "@example.test " not in second_output.getvalue()


@pytest.mark.django_db
def test_seed_demo_requires_force_when_debug_is_false():
    with override_settings(DEBUG=False):
        with pytest.raises(CommandError, match="Pass --force"):
            call_command("seed_demo")
        call_command("seed_demo", force=True, stdout=StringIO())


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
    delete_private_files((evidence.original_path, evidence.display_path, evidence.thumbnail_path))


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
def test_overlapping_active_wards_refuse_ambiguous_report(client, citizen, ward, category):
    polygon = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    Ward.objects.create(
        name="Overlapping Test Ward",
        boundary=MultiPolygon(polygon, srid=4326),
        source="overlap regression fixture",
        effective_from="2026-01-01",
    )
    client.force_login(citizen)

    response = client.post(
        reverse("report"),
        {
            "category": category.pk,
            "latitude": "0",
            "longitude": "0",
            "consent": "on",
            "pin_confirmed": "on",
            "photo": SimpleUploadedFile("overlap.jpg", make_image(), content_type="image/jpeg"),
        },
    )

    assert response.status_code == 200
    assert "multiple active wards" in response.content.decode().lower()
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
    try:
        thumbnail_before = set(private_storage.listdir("thumbnail")[1])
    except FileNotFoundError:
        thumbnail_before = set()
    response = client.post(reverse("report"), {"category": category.pk, "latitude": "0", "longitude": "0", "consent": "on", "pin_confirmed": "on", "photo": SimpleUploadedFile("test.jpg", make_image(), content_type="image/jpeg")})
    assert response.status_code == 200
    assert not Complaint.objects.exists()
    assert not Evidence.objects.exists()
    assert set(private_storage.listdir("original")[1]) == original_before
    assert set(private_storage.listdir("display")[1]) == display_before
    assert set(private_storage.listdir("thumbnail")[1]) == thumbnail_before


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
    delete_private_files((evidence.original_path, evidence.display_path, evidence.thumbnail_path))


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

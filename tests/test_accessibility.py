import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.complaints.models import Complaint
from apps.geography.models import Category, Department, Ward


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a" and "href" in attributes:
            self.links.append(attributes["href"])


def _luminance(color):
    components = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in components]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first, second):
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.fixture
def report_accessibility_case(db):
    citizen = User.objects.create_user(
        email="report-access-citizen@example.test", password="Strong!Password982", name="Test Resident"
    )
    category = Category.objects.create(name="report-accessibility-test")
    return {"citizen": citizen, "category": category}


@pytest.fixture
def triage_accessibility_case(db):
    department = Department.objects.create(name="Accessibility Test Department")
    citizen = User.objects.create_user(
        email="access-citizen@example.test", password="Strong!Password982", name="Test Citizen"
    )
    reviewer = User.objects.create_user(
        email="access-reviewer@example.test",
        password="Strong!Password982",
        name="Test Reviewer",
        role=User.Role.TRIAGE_REVIEWER,
    )
    ring = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(
        name="Accessibility Test Ward",
        boundary=MultiPolygon(ring, srid=4326),
        source="synthetic test fixture",
        effective_from=date(2026, 1, 1),
    )
    category = Category.objects.create(name="accessibility-test", default_department=department)
    complaint = Complaint.objects.create(
        public_id="ASC-ACCESS-0001",
        citizen=citizen,
        category=category,
        description="A synthetic complaint for template accessibility tests.",
        location=Point(0, 0, srid=4326),
        ward=ward,
        status=Complaint.Status.IN_TRIAGE,
        consent_at=timezone.now(),
    )
    return {"citizen": citizen, "reviewer": reviewer, "complaint": complaint}


@pytest.mark.django_db
def test_report_form_has_skip_link_labels_and_keyboard_accessible_map(client, report_accessibility_case):
    client.force_login(report_accessibility_case["citizen"])

    response = client.get(reverse("report"))

    assert response.status_code == 200
    html = response.content.decode()
    assert 'href="#main-content">Skip to main content</a>' in html
    assert '<label for="id_category">Issue category</label>' in html
    assert '<label for="id_description">' in html
    assert '<label for="id_photo">' in html
    assert 'aria-label="Map for selecting a report location"' in html
    assert 'type="button" id="locate-button"' in html
    assert "This platform is not an emergency service." in html


@pytest.mark.django_db
def test_report_validation_errors_are_announced_and_link_to_fields(
    client, report_accessibility_case, monkeypatch
):
    client.force_login(report_accessibility_case["citizen"])
    monkeypatch.setattr("apps.complaints.views.cache.add", lambda *args, **kwargs: True)

    response = client.post(reverse("report"), {"category": ""})

    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="report-error-summary" role="alert" aria-live="assertive" tabindex="-1"' in html
    assert 'href="#id_category"' in html
    assert 'href="#id_photo"' in html
    assert "js/accessibility.js" in html


@pytest.mark.django_db
def test_triage_queue_filters_and_actions_use_labelled_native_controls(client, triage_accessibility_case):
    client.force_login(triage_accessibility_case["reviewer"])

    response = client.get(reverse("triage_queue"))

    assert response.status_code == 200
    html = response.content.decode()
    assert '<label>Status<select name="status">' in html
    assert '<label>Ward<select name="ward">' in html
    assert "<summary>Request more information</summary>" in html
    assert "<summary>Route to a department</summary>" in html
    assert "<summary>Reject complaint</summary>" in html
    assert '<label for="message-' in html
    assert '<label for="department-' in html
    assert '<label for="reject-reason-' in html


def test_keyboard_focus_indicator_meets_three_to_one_contrast():
    stylesheet = Path(__file__).resolve().parents[1] / "static" / "css" / "site.css"
    css = stylesheet.read_text(encoding="utf-8")
    match = re.search(r":focus-visible\s*\{\s*outline:\s*3px solid (#[0-9a-fA-F]{6})", css)

    assert match is not None
    focus_color = match.group(1)
    assert "summary:focus-visible" in css
    for background in ("#ffffff", "#f5f7fa"):
        assert _contrast_ratio(focus_color, background) >= 3


def test_compact_header_layout_starts_before_navigation_runs_out_of_room():
    stylesheet = Path(__file__).resolve().parents[1] / "static" / "css" / "site.css"
    css = stylesheet.read_text(encoding="utf-8")

    assert re.search(r"@media\s*\(max-width:\s*900px\)", css)
    assert ".primary-nav { order: 3; width: 100%; overflow-x: auto;" in css


@pytest.mark.django_db
def test_landing_navigation_targets_real_pages_and_existing_sections(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    parser = _AnchorParser()
    parser.feed(response.content.decode())
    assert "/accounts/login/" in parser.links
    assert "/complaints/new/" in parser.links
    assert "/complaints/" in parser.links
    tracking_response = client.get("/complaints/")
    assert tracking_response.status_code == 302
    assert tracking_response.url.startswith("/accounts/login/?next=")
    assert all(link[1:] in parser.ids for link in parser.links if link.startswith("#"))
    assert not any("#login" == link or "#report" == link for link in parser.links)


def test_report_map_assets_are_vendored_and_location_button_has_status_fallback():
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "static/vendor/bootstrap/bootstrap.min.css.map").is_file()
    assert (project_root / "static/vendor/bootstrap/bootstrap.bundle.min.js.map").is_file()
    assert (project_root / "static/vendor/leaflet/leaflet.js").is_file()
    assert (project_root / "static/vendor/leaflet/leaflet.css").is_file()
    assert (project_root / "static/vendor/leaflet/leaflet.js.map").is_file()
    for image_name in ("layers.png", "layers-2x.png", "marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"):
        assert (project_root / "static/vendor/leaflet/images" / image_name).is_file()
    map_script = (project_root / "static/js/report-map.js").read_text(encoding="utf-8")
    report_template = (project_root / "templates/complaints/report.html").read_text(encoding="utf-8")
    base_settings = (project_root / "config/settings/base.py").read_text(encoding="utf-8")
    assert "navigator.geolocation.getCurrentPosition" in map_script
    assert "Location access was denied" in map_script
    assert 'data-tile-url="{{ map_tile_url }}"' in report_template
    assert "L.tileLayer(mapNode.dataset.tileUrl" in map_script
    assert 'tiles.on("tileerror"' in map_script
    assert 'id="location-status" class="subtle" role="status" aria-live="polite"' in report_template
    assert 'SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"' in base_settings

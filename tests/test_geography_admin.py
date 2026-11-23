from pathlib import Path

import pytest
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.geography.admin import WardAdmin
from apps.geography.models import Category, Department, RoutingRule, Ward


def test_ward_admin_uses_geospatial_editor():
    assert issubclass(WardAdmin, GISModelAdmin)


def test_category_display_label_humanizes_stable_slug():
    category = Category(name="water_leakage")

    assert category.display_label == "Water Leakage"


@pytest.mark.django_db
def test_category_display_label_uses_owner_label_without_changing_slug():
    category = Category.objects.create(name="water_leakage", label="Water leak")
    assert category.name == "water_leakage"
    assert category.display_label == "Water leak"
    assert str(category) == "Water leak"


@pytest.mark.django_db
def test_admin_routing_gap_report_lists_only_categories_without_active_rule(client):
    department = Department.objects.create(name="Report Department")
    category_missing = Category.objects.create(name="missing-route", label="Missing route")
    category_covered = Category.objects.create(name="covered-route", label="Covered route")
    polygon = Polygon(((0, 0), (1, 0), (1, 1), (0, 1), (0, 0)))
    ward = Ward.objects.create(name="Routing report ward", boundary=MultiPolygon(polygon, srid=4326),
                               source="test fixture", effective_from="2026-01-01")
    RoutingRule.objects.create(category=category_covered, ward=ward, department=department, version=1,
                               effective_from=timezone.now())
    staff_admin = User.objects.create_user(
        email="routing-admin@example.test", password="Strong!Password982", name="Routing Admin",
        role=User.Role.ADMIN, is_staff=True,
    )
    client.force_login(staff_admin)
    response = client.get(reverse("admin:geography_category_routing_gaps"), {"ward": ward.pk})
    assert response.status_code == 200
    assert b"Missing route" in response.content
    assert b"Covered route" not in response.content


def test_live_templates_do_not_render_category_slug_directly():
    project_root = Path(__file__).resolve().parents[1]
    templates = (
        project_root / "templates/home.html",
        project_root / "templates/complaints/detail.html",
        project_root / "templates/complaints/my_complaints.html",
        project_root / "templates/console/department_inbox.html",
        project_root / "templates/console/field_tasks.html",
        project_root / "templates/console/field_task_detail.html",
        project_root / "templates/console/triage_queue.html",
    )

    assert all("complaint.category.name" not in path.read_text(encoding="utf-8") for path in templates)

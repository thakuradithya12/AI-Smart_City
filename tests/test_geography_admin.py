from pathlib import Path

import pytest
from django.contrib.gis.admin import GISModelAdmin

from apps.geography.admin import WardAdmin
from apps.geography.models import Category


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

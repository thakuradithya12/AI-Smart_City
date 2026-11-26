import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.complaints.models import Complaint
from apps.geography.models import Category, Department, Ward


EXPECTED_CATEGORIES = {
    "pothole": "Pothole",
    "garbage": "Garbage",
    "drainage": "Drainage",
    "streetlight": "Streetlight",
    "water_leakage": "Water leakage",
    "other": "Other",
}


@pytest.mark.django_db
def test_seed_categories_is_repeatable_and_does_not_create_demo_data():
    call_command("seed_categories")

    assert dict(Category.objects.values_list("name", "label")) == EXPECTED_CATEGORIES
    assert Category.objects.filter(is_active=True).count() == len(EXPECTED_CATEGORIES)
    assert not User.objects.exists()
    assert not Department.objects.exists()
    assert not Ward.objects.exists()
    assert not Complaint.objects.exists()

    Category.objects.filter(name="pothole").update(label="Owner label", default_due_hours=24)
    call_command("seed_categories")

    pothole = Category.objects.get(name="pothole")
    assert pothole.label == "Owner label"
    assert pothole.default_due_hours == 24
    assert Category.objects.count() == len(EXPECTED_CATEGORIES)

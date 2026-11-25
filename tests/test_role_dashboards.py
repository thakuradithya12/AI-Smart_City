import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.complaints.models import Complaint
from apps.geography.models import Category, Department


@pytest.fixture
def dashboard_roles(db):
    department = Department.objects.create(name="Dashboard Department")
    other_department = Department.objects.create(name="Other Dashboard Department")
    citizen = User.objects.create_user(
        phone_number="9876502001", password="Strong!Password982", name="Dashboard Citizen"
    )
    worker = User.objects.create_user(
        phone_number="9876502002", password="Strong!Password982", name="Dashboard Worker",
        role=User.Role.FIELD_WORKER, department=department,
    )
    official = User.objects.create_user(
        phone_number="9876502003", password="Strong!Password982", name="Dashboard Official",
        role=User.Role.DEPARTMENT_OFFICIAL, department=department,
    )
    supervisor = User.objects.create_user(
        phone_number="9876502004", password="Strong!Password982", name="Dashboard Supervisor",
        role=User.Role.SUPERVISOR, department=department,
    )
    admin = User.objects.create_user(
        phone_number="9876502005", password="Strong!Password982", name="Dashboard Admin",
        role=User.Role.ADMIN,
    )
    category = Category.objects.create(name="dashboard-test")

    def complaint(public_id, status, *, owner=citizen, assigned_to=None, routed_department=None):
        return Complaint.objects.create(
            public_id=public_id, citizen=owner, category=category, status=status,
            department=routed_department, assignee=assigned_to,
            location=Point(78.48, 17.38, srid=4326), consent_at=timezone.now(),
        )

    citizen_complaint = complaint("DASH-CITIZEN", Complaint.Status.IN_TRIAGE)
    department_complaint = complaint(
        "DASH-DEPT", Complaint.Status.ROUTED, routed_department=department
    )
    worker_complaint = complaint(
        "DASH-WORKER", Complaint.Status.ASSIGNED,
        assigned_to=worker, routed_department=department,
    )
    verification_complaint = complaint(
        "DASH-VERIFY", Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        assigned_to=worker, routed_department=department,
    )
    complaint(
        "DASH-OTHER", Complaint.Status.ROUTED, routed_department=other_department
    )
    return {
        "roles": {
            "citizen": citizen,
            "field_worker": worker,
            "department_official": official,
            "supervisor": supervisor,
            "admin": admin,
        },
        "expected_visible": {
            "citizen": {citizen_complaint.public_id},
            "field_worker": {worker_complaint.public_id, verification_complaint.public_id},
            "department_official": {department_complaint.public_id, worker_complaint.public_id, verification_complaint.public_id},
            "supervisor": {department_complaint.public_id, worker_complaint.public_id, verification_complaint.public_id},
            "admin": {citizen_complaint.public_id, department_complaint.public_id, worker_complaint.public_id, verification_complaint.public_id, "DASH-OTHER"},
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "title", "metric_label"),
    [
        ("citizen", "Your reports", "My reports"),
        ("field_worker", "My field work", "Assigned tasks"),
        ("department_official", "Department overview", "Routed to us"),
        ("supervisor", "Supervisor overview", "Awaiting verification"),
        ("admin", "City operations", "In triage"),
    ],
)
def test_role_dashboard_uses_role_scoped_complaints_and_quick_links(
    client, dashboard_roles, role, title, metric_label,
):
    client.force_login(dashboard_roles["roles"][role])

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert response.context["dashboard_title"] == title
    assert {item.public_id for item in response.context["recent_complaints"]} <= dashboard_roles["expected_visible"][role]
    assert metric_label in {metric["label"] for metric in response.context["dashboard_metrics"]}
    for public_id in set().union(*dashboard_roles["expected_visible"].values()) - dashboard_roles["expected_visible"][role]:
        assert public_id.encode() not in response.content

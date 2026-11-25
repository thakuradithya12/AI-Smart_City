import csv
from io import StringIO

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint
from apps.geography.models import Category, Department


@pytest.fixture
def audit_setup(db):
    department = Department.objects.create(name="Audit Department")
    other_department = Department.objects.create(name="Other Audit Department")
    citizen = User.objects.create_user(
        phone_number="9876503001", password="Strong!Password982", name="Audit Citizen"
    )
    supervisor = User.objects.create_user(
        phone_number="9876503002", password="Strong!Password982", name="Audit Supervisor",
        role=User.Role.SUPERVISOR, department=department,
    )
    admin = User.objects.create_user(
        phone_number="9876503003", password="Strong!Password982", name="Audit Admin",
        role=User.Role.ADMIN,
    )
    category = Category.objects.create(name="audit-test")
    own = Complaint.objects.create(
        public_id="AUDIT-OWN", citizen=citizen, category=category,
        department=department, status=Complaint.Status.ACKNOWLEDGED,
        location=Point(78.48, 17.38, srid=4326), consent_at=timezone.now(),
    )
    other = Complaint.objects.create(
        public_id="AUDIT-OTHER", citizen=citizen, category=category,
        department=other_department, status=Complaint.Status.ACKNOWLEDGED,
        location=Point(78.48, 17.38, srid=4326), consent_at=timezone.now(),
    )
    own_event = AuditEvent.objects.create(
        actor=supervisor, role=User.Role.SUPERVISOR, action="department_action",
        object_type="Complaint", object_id=str(own.pk), before={}, after={"status": "routed"},
    )
    own_related_event = AuditEvent.objects.create(
        actor=supervisor, role=User.Role.SUPERVISOR, action="evidence_uploaded",
        object_type="Evidence", object_id="15", before={}, after={"complaint_id": own.pk},
    )
    other_event = AuditEvent.objects.create(
        actor=admin, role=User.Role.ADMIN, action="other_department_action",
        object_type="Complaint", object_id=str(other.pk), before={}, after={"status": "routed"},
    )
    return {
        "supervisor": supervisor,
        "admin": admin,
        "own_events": {own_event.pk, own_related_event.pk},
        "all_events": {own_event.pk, own_related_event.pk, other_event.pk},
    }


@pytest.mark.django_db
def test_supervisor_audit_workspace_is_scoped_to_visible_department(client, audit_setup):
    client.force_login(audit_setup["supervisor"])

    response = client.get(reverse("audit_workspace"))

    assert response.status_code == 200
    assert {event.pk for event in response.context["events"]} == audit_setup["own_events"]
    assert b"other_department_action" not in response.content


@pytest.mark.django_db
def test_admin_audit_workspace_and_csv_include_all_events(client, audit_setup):
    client.force_login(audit_setup["admin"])

    page = client.get(reverse("audit_workspace"))
    export = client.get(reverse("audit_export_csv"))

    assert {event.pk for event in page.context["events"]} == audit_setup["all_events"]
    assert export["Content-Disposition"] == 'attachment; filename="audit-events.csv"'
    assert export["Cache-Control"] == "private, no-store"
    rows = list(csv.reader(StringIO(export.content.decode("utf-8"))))
    assert len(rows) == 4


@pytest.mark.django_db
def test_audit_workspace_denies_citizens(client, audit_setup):
    citizen = User.objects.get(phone_number="+919876503001")
    client.force_login(citizen)

    assert client.get(reverse("audit_workspace")).status_code == 404
    assert client.get(reverse("audit_export_csv")).status_code == 404


@pytest.mark.django_db
def test_csv_export_prefixes_formula_cells(client, audit_setup):
    AuditEvent.objects.create(
        actor=audit_setup["admin"], role=User.Role.ADMIN, action="=1+1",
        object_type="Complaint", object_id="+17", before={}, after={}, reason="@SUM(A1:A2)",
    )
    client.force_login(audit_setup["admin"])

    response = client.get(reverse("audit_export_csv"))

    rows = list(csv.reader(StringIO(response.content.decode("utf-8"))))
    formula_row = next(row for row in rows[1:] if row[3] == "'=1+1")
    assert formula_row[5] == "'+17"
    assert formula_row[8] == "'@SUM(A1:A2)"

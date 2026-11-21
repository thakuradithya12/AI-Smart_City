from datetime import date, timedelta

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, StatusEvent
from apps.geography.models import Category, Department, RoutingRule, Ward


@pytest.fixture
def console_setup(db):
    department_a = Department.objects.create(name="Road Department")
    department_b = Department.objects.create(name="Water Department")
    citizen = User.objects.create_user(email="console-citizen@example.test", password="Strong!Password982", name="Console Citizen")
    reviewer = User.objects.create_user(email="console-reviewer@example.test", password="Strong!Password982", name="Console Reviewer", role=User.Role.TRIAGE_REVIEWER)
    official = User.objects.create_user(email="console-official@example.test", password="Strong!Password982", name="Road Official", role=User.Role.DEPARTMENT_OFFICIAL, department=department_a)
    field_worker = User.objects.create_user(email="console-worker@example.test", password="Strong!Password982", name="Road Worker", role=User.Role.FIELD_WORKER, department=department_a)
    other_official = User.objects.create_user(email="water-official@example.test", password="Strong!Password982", name="Water Official", role=User.Role.DEPARTMENT_OFFICIAL, department=department_b)
    admin = User.objects.create_user(email="console-admin@example.test", password="Strong!Password982", name="Console Admin", role=User.Role.ADMIN)
    ring = Polygon(((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)))
    ward = Ward.objects.create(name="Console Ward", boundary=MultiPolygon(ring, srid=4326), source="hand-written test polygon", effective_from=date(2026, 1, 1))
    category = Category.objects.create(name="console-test", default_department=department_a)
    rule = RoutingRule.objects.create(category=category, ward=ward, department=department_a, version=1, effective_from=timezone.now())
    return locals()


def make_complaint(setup, *, status=Complaint.Status.IN_TRIAGE, department=None, public_id="CON-1"):
    return Complaint.objects.create(
        public_id=public_id,
        citizen=setup["citizen"],
        category=setup["category"],
        location=Point(0, 0, srid=4326),
        ward=setup["ward"],
        department=department,
        status=status,
        consent_at="2026-01-01T00:00:00Z",
    )


@pytest.mark.django_db
def test_triage_queue_scopes_role_and_hides_citizen_email(client, console_setup):
    complaint = make_complaint(console_setup)
    client.force_login(console_setup["reviewer"])
    response = client.get(reverse("triage_queue"))
    assert response.status_code == 200
    assert complaint.public_id.encode() in response.content
    assert b"Console Citizen" in response.content
    assert b"console-citizen@example.test" not in response.content

    client.force_login(console_setup["citizen"])
    assert client.get(reverse("triage_queue")).status_code == 404


@pytest.mark.django_db
def test_triage_routes_from_ward_category_rule_and_audits(client, console_setup):
    complaint = make_complaint(console_setup)
    client.force_login(console_setup["reviewer"])
    response = client.post(reverse("route_complaint", args=[complaint.pk]), {})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.ROUTED
    assert complaint.department == console_setup["department_a"]
    event = AuditEvent.objects.get(action="complaint_routed", object_id=str(complaint.pk))
    assert event.after == {"department_id": console_setup["department_a"].pk, "routing_rule_version": console_setup["rule"].version, "overridden": False}
    status_event = StatusEvent.objects.get(complaint=complaint)
    assert status_event.from_status == Complaint.Status.IN_TRIAGE
    assert status_event.to_status == Complaint.Status.ROUTED


@pytest.mark.django_db
def test_routing_prefers_active_ward_rule_over_newer_global_rule_and_audits_version(client, console_setup):
    setup = console_setup
    global_rule = RoutingRule.objects.create(
        category=setup["category"],
        ward=None,
        department=setup["department_b"],
        version=9,
        effective_from=timezone.now(),
    )
    complaint = make_complaint(setup, public_id="CON-WARD-PRECEDENCE")
    client.force_login(setup["reviewer"])

    response = client.post(reverse("route_complaint", args=[complaint.pk]), {})

    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.department == setup["department_a"]
    event = AuditEvent.objects.get(action="complaint_routed", object_id=str(complaint.pk))
    assert event.after["routing_rule_version"] == setup["rule"].version
    assert event.after["routing_rule_version"] != global_rule.version


@pytest.mark.django_db
def test_future_ward_rule_is_ignored_in_favor_of_active_global_rule(client, console_setup):
    setup = console_setup
    setup["rule"].effective_from = timezone.now() + timedelta(days=1)
    setup["rule"].save(update_fields=["effective_from"])
    RoutingRule.objects.create(
        category=setup["category"],
        ward=setup["ward"],
        department=setup["department_b"],
        version=2,
        effective_from=timezone.now() + timedelta(days=2),
    )
    global_rule = RoutingRule.objects.create(
        category=setup["category"],
        ward=None,
        department=setup["department_b"],
        version=1,
        effective_from=timezone.now() - timedelta(days=2),
    )
    complaint = make_complaint(setup, public_id="CON-FUTURE-RULE")
    client.force_login(setup["reviewer"])

    response = client.post(reverse("route_complaint", args=[complaint.pk]), {})

    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.department == global_rule.department
    event = AuditEvent.objects.get(action="complaint_routed", object_id=str(complaint.pk))
    assert event.after["routing_rule_version"] == global_rule.version


@pytest.mark.django_db
def test_safety_critical_category_is_warned_in_triage_queue(client, console_setup):
    setup = console_setup
    setup["category"].is_safety_critical = True
    setup["category"].save(update_fields=["is_safety_critical"])
    complaint = make_complaint(setup, public_id="CON-SAFETY-WARNING")
    client.force_login(setup["reviewer"])

    response = client.get(reverse("triage_queue"))

    assert response.status_code == 200
    assert b"Safety critical" in response.content
    assert complaint.public_id.encode() in response.content


@pytest.mark.django_db
def test_route_rolls_back_status_and_events_if_routing_audit_fails(client, console_setup, monkeypatch):
    complaint = make_complaint(console_setup)
    client.force_login(console_setup["reviewer"])
    original_save = AuditEvent.save

    def fail_routing_event(self, *args, **kwargs):
        if self.action == "complaint_routed":
            raise RuntimeError("injected routing audit failure")
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(AuditEvent, "save", fail_routing_event)
    with pytest.raises(RuntimeError, match="injected routing audit failure"):
        client.post(reverse("route_complaint", args=[complaint.pk]), {})

    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_TRIAGE
    assert complaint.department is None
    assert not StatusEvent.objects.filter(complaint=complaint).exists()
    assert not AuditEvent.objects.filter(object_id=str(complaint.pk)).exists()


@pytest.mark.django_db
def test_triage_override_requires_reason_and_admin_override_is_flagged(client, console_setup):
    complaint = make_complaint(console_setup)
    client.force_login(console_setup["reviewer"])
    route_url = reverse("route_complaint", args=[complaint.pk])
    client.post(route_url, {"department": console_setup["department_b"].pk})
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_TRIAGE
    assert complaint.department is None
    client.post(route_url, {"department": console_setup["department_b"].pk, "reason": "Water team owns this asset."})
    complaint.refresh_from_db()
    assert complaint.department == console_setup["department_b"]
    assert AuditEvent.objects.filter(action="complaint_routed", object_id=str(complaint.pk), after__overridden=True).exists()

    admin_complaint = make_complaint(console_setup, public_id="CON-2")
    client.force_login(console_setup["admin"])
    client.post(reverse("route_complaint", args=[admin_complaint.pk]), {})
    admin_complaint.refresh_from_db()
    assert admin_complaint.status == Complaint.Status.IN_TRIAGE
    client.post(reverse("route_complaint", args=[admin_complaint.pk]), {"reason": "Approved admin override."})
    admin_complaint.refresh_from_db()
    assert admin_complaint.status == Complaint.Status.ROUTED
    assert AuditEvent.objects.filter(action="admin_override", object_id=str(admin_complaint.pk), reason="Approved admin override.").exists()


@pytest.mark.django_db
def test_triage_reject_requires_free_text_reason_and_audits(client, console_setup):
    complaint = make_complaint(console_setup)
    client.force_login(console_setup["reviewer"])
    reject_url = reverse("reject_complaint", args=[complaint.pk])
    client.post(reject_url, {"reason": " "})
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_TRIAGE
    client.post(reject_url, {"reason": "Outside supported services."})
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.REJECTED
    assert StatusEvent.objects.get(complaint=complaint).reason == "Outside supported services."
    assert AuditEvent.objects.filter(action="status_transition", object_id=str(complaint.pk), reason="Outside supported services.").exists()


@pytest.mark.django_db
def test_department_inbox_is_scoped_and_acknowledges(client, console_setup):
    own = make_complaint(console_setup, status=Complaint.Status.ROUTED, department=console_setup["department_a"], public_id="CON-3")
    other = make_complaint(console_setup, status=Complaint.Status.ROUTED, department=console_setup["department_b"], public_id="CON-4")
    client.force_login(console_setup["official"])
    response = client.get(reverse("department_inbox"))
    assert own.public_id.encode() in response.content
    assert other.public_id.encode() not in response.content
    assert b"console-citizen@example.test" not in response.content
    response = client.post(reverse("acknowledge_complaint", args=[own.pk]))
    assert response.status_code == 302
    own.refresh_from_db()
    assert own.status == Complaint.Status.ACKNOWLEDGED

    client.force_login(console_setup["other_official"])
    assert client.post(reverse("acknowledge_complaint", args=[own.pk])).status_code == 404


@pytest.mark.django_db
def test_department_transfer_returns_to_triage_with_reason(client, console_setup):
    complaint = make_complaint(console_setup, status=Complaint.Status.ROUTED, department=console_setup["department_a"], public_id="CON-5")
    client.force_login(console_setup["official"])
    response = client.post(reverse("transfer_to_triage", args=[complaint.pk]), {"reason": "This is maintained by water services."})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.IN_TRIAGE
    event = StatusEvent.objects.get(complaint=complaint)
    assert event.reason == "This is maintained by water services."
    assert AuditEvent.objects.filter(action="status_transition", object_id=str(complaint.pk), reason=event.reason).exists()


@pytest.mark.django_db
def test_department_assignment_restricts_worker_to_same_department(client, console_setup):
    complaint = make_complaint(console_setup, status=Complaint.Status.ACKNOWLEDGED, department=console_setup["department_a"], public_id="CON-6")
    client.force_login(console_setup["official"])
    response = client.post(reverse("assign_complaint", args=[complaint.pk]), {"assignee": console_setup["field_worker"].pk})
    assert response.status_code == 302
    complaint.refresh_from_db()
    assert complaint.status == Complaint.Status.ASSIGNED
    assert complaint.assignee == console_setup["field_worker"]
    audit = AuditEvent.objects.get(action="status_transition", object_id=str(complaint.pk))
    assert audit.after["assignee_id"] == console_setup["field_worker"].pk

    complaint2 = make_complaint(console_setup, status=Complaint.Status.ACKNOWLEDGED, department=console_setup["department_a"], public_id="CON-7")
    response = client.post(reverse("assign_complaint", args=[complaint2.pk]), {"assignee": console_setup["other_official"].pk})
    assert response.status_code == 302
    complaint2.refresh_from_db()
    assert complaint2.status == Complaint.Status.ACKNOWLEDGED

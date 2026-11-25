from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.accounts.models import User
from apps.complaints.models import Complaint, Resolution, StatusEvent
from apps.geography.models import Category, Department
from apps.notifications.models import Notification
from apps.notifications.services import enqueue_citizen_reminders


@pytest.fixture
def pending_claim(db):
    department = Department.objects.create(name="Reminder Department")
    citizen = User.objects.create_user(
        phone_number="9876501111", password="Strong!Password982", name="Reminder Citizen"
    )
    worker = User.objects.create_user(
        phone_number="9876501112", password="Strong!Password982", name="Reminder Worker",
        role=User.Role.FIELD_WORKER, department=department,
    )
    category = Category.objects.create(name="reminder-test", default_department=department)
    complaint = Complaint.objects.create(
        public_id="REMINDER-TEST", citizen=citizen, category=category,
        department=department, assignee=worker, status=Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        location=Point(78.48, 17.38, srid=4326), consent_at=timezone.now(),
    )
    claim_time = timezone.now() - timedelta(days=3)
    Resolution.objects.create(
        complaint=complaint, claimed_by=worker, claimed_at=claim_time, claim_note="Work complete."
    )
    StatusEvent.objects.create(
        complaint=complaint, from_status=Complaint.Status.IN_PROGRESS,
        to_status=Complaint.Status.RESOLVED_PENDING_VERIFICATION,
        actor=worker, role=User.Role.FIELD_WORKER, created_at=claim_time,
    )
    return complaint, claim_time


@pytest.mark.django_db
def test_first_reminder_queues_after_three_days_once_and_never_closes(pending_claim, settings):
    complaint, claim_time = pending_claim
    settings.CITIZEN_REMINDER_DAYS = 3
    status_events_before = StatusEvent.objects.filter(complaint=complaint).count()
    resolution = Resolution.objects.get(complaint=complaint)

    before_deadline = claim_time + timedelta(days=3) - timedelta(seconds=1)
    assert enqueue_citizen_reminders(now=before_deadline) == 0

    after_deadline = claim_time + timedelta(days=3)
    assert enqueue_citizen_reminders(now=after_deadline) == 1
    assert enqueue_citizen_reminders(now=after_deadline + timedelta(hours=1)) == 0

    complaint.refresh_from_db()
    resolution.refresh_from_db()
    reminder = Notification.objects.get(complaint=complaint, event=Notification.Event.CITIZEN_REMINDER)
    assert reminder.recipient == complaint.citizen
    assert complaint.status == Complaint.Status.RESOLVED_PENDING_VERIFICATION
    assert resolution.verified_by is None and resolution.verified_at is None
    assert StatusEvent.objects.filter(complaint=complaint).count() == status_events_before

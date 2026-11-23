from django.contrib.gis.db import models
from django.conf import settings
from django.utils import timezone


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValueError("Status events are append-only")

    def delete(self):
        raise ValueError("Status events are append-only")


class ComplaintQuerySet(models.QuerySet):
    def visible_to(self, user):
        # Every complaint lookup must be scoped by role before a view returns data.
        if not user.is_authenticated or not user.is_active:
            return self.none()
        if user.is_superuser or user.role == "admin" or user.role == "triage_reviewer":
            return self
        if user.role == "citizen":
            return self.filter(citizen=user)
        if user.role in {"department_official", "supervisor"}:
            # Staff without a department must never inherit visibility over unassigned reports.
            return self.filter(department_id=user.department_id) if user.department_id else self.none()
        if user.role == "field_worker":
            return self.filter(assignee=user)
        return self.none()

class Complaint(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        IN_TRIAGE = "in_triage", "In triage"
        INFO_REQUESTED = "info_requested", "Information requested"
        ROUTED = "routed", "Routed"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED_PENDING_VERIFICATION = "resolved_pending_verification", "Awaiting verification"
        VERIFIED_CLOSED = "verified_closed", "Verified closed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        REOPENED = "reopened", "Reopened"

    public_id = models.CharField(max_length=32, unique=True, blank=True)
    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="complaints")
    category = models.ForeignKey("geography.Category", on_delete=models.PROTECT)
    suggested_category = models.ForeignKey("geography.Category", null=True, blank=True, on_delete=models.SET_NULL, related_name="suggested_complaints")
    description = models.TextField(blank=True)
    landmark = models.CharField(max_length=160, blank=True)
    location = models.PointField(srid=4326)
    gps_accuracy_m = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    ward = models.ForeignKey("geography.Ward", null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey("geography.Department", null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.SUBMITTED)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="assigned_complaints")
    due_at = models.DateTimeField(null=True, blank=True)
    consent_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    duplicate_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    objects = ComplaintQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["status", "due_at"], name="complaint_status_due_idx"),
            models.Index(fields=["department", "status"], name="complaint_dept_status_idx"),
            models.Index(fields=["ward", "status"], name="complaint_ward_status_idx"),
            models.Index(fields=["created_at"], name="complaint_created_idx"),
        ]

    @property
    def is_overdue(self):
        return bool(
            self.due_at and self.due_at < timezone.now()
            and self.status not in {self.Status.VERIFIED_CLOSED, self.Status.REJECTED, self.Status.CANCELLED}
        )

class Evidence(models.Model):
    class Kind(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        FIELD_BEFORE = "field_before", "Field before"
        FIELD_AFTER = "field_after", "Field after"
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="evidence")
    kind = models.CharField(max_length=24, choices=Kind.choices)
    original_path = models.CharField(max_length=500)
    display_path = models.CharField(max_length=500)
    thumbnail_path = models.CharField(max_length=500, blank=True, default="")
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(default=timezone.now)

class StatusEvent(models.Model):
    objects = models.Manager.from_queryset(AppendOnlyQuerySet)()

    complaint = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name="status_events")
    from_status = models.CharField(max_length=40, blank=True)
    to_status = models.CharField(max_length=40)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    role = models.CharField(max_length=32)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Status events are append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Status events are append-only")

class Resolution(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name="resolution")
    claimed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="resolution_claims")
    claimed_at = models.DateTimeField(default=timezone.now)
    claim_note = models.TextField()
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="resolution_verifications")
    verified_at = models.DateTimeField(null=True, blank=True)
    method = models.CharField(max_length=40, blank=True)
    outcome = models.CharField(max_length=40, blank=True)

class ComplaintMessage(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

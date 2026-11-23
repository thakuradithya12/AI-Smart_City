from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user):
        # Inbox rows must satisfy both recipient ownership and complaint visibility.
        if not user.is_authenticated or not user.is_active:
            return self.none()
        from apps.complaints.models import Complaint

        return self.filter(recipient=user, complaint__in=Complaint.objects.visible_to(user))


class Notification(models.Model):
    class Event(models.TextChoices):
        REPORT_RECEIVED = "report_received", "Report received"
        INFORMATION_REQUESTED = "information_requested", "More information requested"
        ROUTED = "routed", "Assigned to a department"
        WORK_CLAIMED = "work_claimed", "Work marked complete"
        VERIFIED_CLOSED = "verified_closed", "Complaint verified and closed"
        REOPENED = "reopened", "Complaint reopened"
        ASSIGNED_TO_ME = "assigned_to_me", "Work assigned to you"
        OVERDUE = "overdue", "Complaint overdue"
        CITIZEN_REMINDER = "citizen_reminder", "Please review the work update"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    complaint = models.ForeignKey(
        "complaints.Complaint", on_delete=models.CASCADE, related_name="notifications"
    )
    event = models.CharField(max_length=32, choices=Event.choices)
    status = models.CharField(max_length=40)
    event_key = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    email_skipped_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    last_error = models.CharField(max_length=120, blank=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["recipient", "read_at", "created_at"], name="notification_inbox_idx"),
            models.Index(fields=["sent_at", "next_attempt_at"], name="notification_email_idx"),
        ]

    def __str__(self):
        return f"{self.get_event_display()} — {self.complaint.public_id}"

    @property
    def status_label(self):
        from apps.complaints.models import Complaint

        return dict(Complaint.Status.choices).get(self.status, self.status.replace("_", " ").title())

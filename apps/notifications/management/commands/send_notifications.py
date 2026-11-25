from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.complaints.models import Complaint
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = "Deliver a bounded batch of queued complaint notification emails."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=settings.NOTIFICATION_BATCH_SIZE)

    def _claim(self, notification_id, now):
        max_attempts = settings.NOTIFICATION_MAX_ATTEMPTS
        with transaction.atomic():
            notification = Notification.objects.select_for_update().select_related(
                "recipient", "complaint"
            ).get(pk=notification_id)
            if notification.sent_at or notification.email_skipped_at:
                return None
            if notification.attempts >= max_attempts or (notification.next_attempt_at and notification.next_attempt_at > now):
                return None
            if not notification.recipient.email:
                notification.email_skipped_at = now
                notification.last_error = "No email address; in-app only"
                notification.save(update_fields=["email_skipped_at", "last_error"])
                return None

            # Reserve the row briefly; attempts count completed sends so a crashed worker can retry.
            notification.next_attempt_at = now + timedelta(seconds=settings.NOTIFICATION_SEND_LEASE_SECONDS)
            notification.save(update_fields=["next_attempt_at"])
            return notification

    def handle(self, *args, **options):
        limit = options["limit"]
        if not 1 <= limit <= 500:
            raise CommandError("--limit must be between 1 and 500.")

        now = timezone.now()
        notification_ids = list(
            Notification.objects.filter(
                sent_at__isnull=True,
                email_skipped_at__isnull=True,
                attempts__lt=settings.NOTIFICATION_MAX_ATTEMPTS,
                next_attempt_at__lte=now,
            ).order_by("created_at", "pk").values_list("pk", flat=True)[:limit]
        )
        sent = failed = skipped = 0
        statuses = dict(Complaint.Status.choices)
        for notification_id in notification_ids:
            notification = self._claim(notification_id, timezone.now())
            if notification is None:
                skipped += 1
                continue

            detail_url = f"{settings.SITE_BASE_URL.rstrip('/')}{reverse('complaint_detail', args=[notification.complaint_id])}"
            status = statuses.get(notification.status, notification.status)
            # Email body is intentionally limited to the public id, status and authorized detail link.
            body = f"{notification.complaint.public_id}\n{status}\n{detail_url}"
            try:
                delivered = send_mail(
                    subject="Complaint update",
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient.email],
                    fail_silently=False,
                )
                if delivered != 1:
                    raise RuntimeError("Email backend did not accept the message")
            except Exception as exc:
                notification.attempts += 1
                notification.last_error = type(exc).__name__
                if notification.attempts >= settings.NOTIFICATION_MAX_ATTEMPTS:
                    notification.next_attempt_at = None
                else:
                    delay = settings.NOTIFICATION_RETRY_DELAYS_SECONDS[
                        min(notification.attempts - 1, len(settings.NOTIFICATION_RETRY_DELAYS_SECONDS) - 1)
                    ]
                    notification.next_attempt_at = timezone.now() + timedelta(seconds=delay)
                notification.save(update_fields=["attempts", "last_error", "next_attempt_at"])
                failed += 1
            else:
                notification.attempts += 1
                notification.sent_at = timezone.now()
                notification.next_attempt_at = None
                notification.last_error = ""
                notification.save(update_fields=["attempts", "sent_at", "next_attempt_at", "last_error"])
                sent += 1

        self.stdout.write(
            self.style.SUCCESS(f"Processed {len(notification_ids)} notifications: {sent} sent, {failed} failed, {skipped} skipped.")
        )

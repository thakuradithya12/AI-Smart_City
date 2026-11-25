from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounts.models import PrivacyDeletionRequest, User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, ComplaintMessage, Evidence, Resolution, StatusEvent
from apps.complaints.services import delete_private_files
from apps.notifications.models import Notification


PURGE_ADVISORY_LOCK_ID = 0x4153435055524745


class Command(BaseCommand):
    help = "Anonymise deletion requests and purge expired complaint details and evidence."

    def _try_lock(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [PURGE_ADVISORY_LOCK_ID])
            return cursor.fetchone()[0]

    def _unlock(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [PURGE_ADVISORY_LOCK_ID])

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("purge_expired requires PostgreSQL advisory locks.")
        connection.ensure_connection()
        if not self._try_lock():
            self.stdout.write("Another purge_expired run holds the lock; exiting.")
            return
        try:
            now = timezone.now()
            anonymised = self._process_deletion_requests(now)
            anonymised += self._anonymise_old_inactive_accounts(now)
            purged = self._purge_retained_complaints(now)
        finally:
            self._unlock()
        self.stdout.write(f"Anonymised {anonymised} account(s); purged {purged} complaint record(s).")

    @staticmethod
    def _anonymise_user(user):
        # Preserve the user row so immutable audit/status events keep a stable, anonymised actor reference.
        user.name = "Deleted user"
        user.phone_number = None
        user.email = None
        user.username = f"deleted-user-{user.pk}"
        user.first_name = ""
        user.last_name = ""
        user.last_login = None
        user.set_unusable_password()
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=[
            "name", "phone_number", "email", "username", "first_name", "last_name",
            "last_login", "password", "is_active", "is_staff", "is_superuser",
        ])
        user.groups.clear()
        user.user_permissions.clear()
        Notification.objects.filter(recipient=user).delete()

    def _process_deletion_requests(self, now):
        count = 0
        request_ids = PrivacyDeletionRequest.objects.filter(
            processed_at__isnull=True
        ).order_by("requested_at", "pk").values_list("pk", flat=True)
        for request_id in request_ids.iterator(chunk_size=100):
            with transaction.atomic():
                # skip_locked makes an overlapping command leave work claimed by its peer alone.
                deletion_request = PrivacyDeletionRequest.objects.select_for_update(skip_locked=True).filter(
                    pk=request_id, processed_at__isnull=True
                ).first()
                if deletion_request is None:
                    continue
                user = User.objects.select_for_update().get(pk=deletion_request.user_id)
                AuditEvent.objects.create(
                    actor=user,
                    role=user.role,
                    action="privacy_deletion_processed",
                    object_type="User",
                    object_id=str(user.pk),
                    after={"account_anonymized": True},
                    reason="The account was anonymised after a citizen deletion request.",
                )
                self._anonymise_user(user)
                deletion_request.processed_at = now
                deletion_request.save(update_fields=["processed_at"])
                count += 1
        return count

    def _anonymise_old_inactive_accounts(self, now):
        cutoff = now - timedelta(days=settings.INACTIVE_ACCOUNT_RETENTION_DAYS)
        users = User.objects.filter(is_active=False).annotate(
            inactive_since=Coalesce("last_login", "date_joined")
        ).filter(inactive_since__lte=cutoff).exclude(
            phone_number__isnull=True, email__isnull=True, name="Deleted user"
        ).order_by("pk")
        count = 0
        for user_id in users.values_list("pk", flat=True).iterator(chunk_size=100):
            with transaction.atomic():
                user = User.objects.select_for_update().filter(pk=user_id, is_active=False).first()
                if user and (user.phone_number or user.email or user.name != "Deleted user"):
                    self._anonymise_user(user)
                    count += 1
        return count

    def _purge_retained_complaints(self, now):
        retention = {
            Complaint.Status.VERIFIED_CLOSED: settings.CLOSED_PHOTO_RETENTION_DAYS,
            Complaint.Status.REJECTED: settings.REJECTED_CANCELLED_RETENTION_DAYS,
            Complaint.Status.CANCELLED: settings.REJECTED_CANCELLED_RETENTION_DAYS,
        }
        purged_count = 0
        last_status_time = StatusEvent.objects.filter(
            complaint_id=OuterRef("pk"), to_status=OuterRef("status")
        ).order_by("-created_at").values("created_at")[:1]
        for status, retention_days in retention.items():
            cutoff = now - timedelta(days=retention_days)
            eligible = Complaint.objects.filter(
                status=status, retention_purged_at__isnull=True
            ).annotate(closed_at=Subquery(last_status_time)).filter(closed_at__lte=cutoff)
            for complaint_id in eligible.values_list("pk", flat=True).iterator(chunk_size=100):
                with transaction.atomic():
                    # Lock each complaint so parallel runs cannot purge its retained data twice.
                    complaint = Complaint.objects.select_for_update(skip_locked=True).filter(
                        pk=complaint_id, status=status, retention_purged_at__isnull=True
                    ).first()
                    if complaint is None:
                        continue
                    paths = list(
                        Evidence.objects.filter(complaint=complaint).values_list(
                            "original_path", "display_path", "thumbnail_path"
                        )
                    )
                    Evidence.objects.filter(complaint=complaint).delete()
                    ComplaintMessage.objects.filter(complaint=complaint).update(body="")
                    Resolution.objects.filter(complaint=complaint).update(claim_note="")
                    complaint.description = ""
                    complaint.landmark = ""
                    complaint.location = None
                    complaint.gps_accuracy_m = None
                    complaint.due_at = None
                    complaint.duplicate_of = None
                    complaint.retention_purged_at = now
                    complaint.save(update_fields=[
                        "description", "landmark", "location", "gps_accuracy_m", "due_at",
                        "duplicate_of", "retention_purged_at",
                    ])
                    paths_to_remove = [path for group in paths for path in group if path]
                    transaction.on_commit(lambda paths=paths_to_remove: delete_private_files(paths))
                    purged_count += 1
        return purged_count

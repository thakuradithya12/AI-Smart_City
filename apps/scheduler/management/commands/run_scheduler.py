import time

from django.conf import settings
from django.core.management import call_command, get_commands
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

from apps.scheduler.models import SchedulerHeartbeat


# PostgreSQL advisory locks are session scoped, so this connection holds leadership for the process lifetime.
SCHEDULER_LOCK_ID = 0x4153435343484544
JOBS = {
    "expire_info_requests": 60,
    "send_notifications": 30,
    "check_sla": 300,
    "purge_expired": 3600,
}


class Command(BaseCommand):
    help = "Run periodic maintenance commands under a PostgreSQL advisory lock."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run due jobs once and exit.")
        parser.add_argument("--poll-seconds", type=int, default=settings.SCHEDULER_POLL_SECONDS)

    def _try_lock(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [SCHEDULER_LOCK_ID])
            return cursor.fetchone()[0]

    def _unlock(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [SCHEDULER_LOCK_ID])

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("run_scheduler requires PostgreSQL advisory locks.")
        poll_seconds = options["poll_seconds"]
        if not 1 <= poll_seconds <= 3600:
            raise CommandError("--poll-seconds must be between 1 and 3600.")
        connection.ensure_connection()
        if not self._try_lock():
            self.stdout.write("Another scheduler holds the advisory lock; exiting.")
            return

        due_at = {name: 0.0 for name in JOBS}
        commands = get_commands()
        missing_reported = set()
        failed_jobs = 0
        last_job = ""
        try:
            while True:
                now_monotonic = time.monotonic()
                for name, interval in JOBS.items():
                    if now_monotonic < due_at[name]:
                        continue
                    # Tasks later in the authorized sequence may not yet have added their command.
                    if name in commands:
                        try:
                            call_command(name)
                            last_job = name
                        except Exception:
                            failed_jobs += 1
                            last_job = f"failed:{name}"
                            self.stderr.write(self.style.ERROR(f"Scheduled command failed: {name}"))
                    elif name not in missing_reported:
                        missing_reported.add(name)
                        self.stderr.write(self.style.WARNING(f"Scheduled command is not installed yet: {name}"))
                    due_at[name] = time.monotonic() + interval

                SchedulerHeartbeat.objects.update_or_create(
                    singleton=1,
                    defaults={"last_seen_at": timezone.now(), "last_job": last_job, "failed_jobs": failed_jobs},
                )
                if options["once"]:
                    break
                time.sleep(poll_seconds)
        finally:
            self._unlock()

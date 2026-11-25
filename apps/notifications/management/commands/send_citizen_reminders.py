from django.core.management.base import BaseCommand

from apps.notifications.services import enqueue_citizen_reminders


class Command(BaseCommand):
    help = "Queue one reminder for each resolution awaiting citizen verification for three days."

    def handle(self, *args, **options):
        created = enqueue_citizen_reminders()
        self.stdout.write(self.style.SUCCESS(f"Queued {created} citizen reminder(s)."))

from django.core.management.base import BaseCommand

from apps.geography.models import Category


REPORT_CATEGORIES = {
    "pothole": "Pothole",
    "garbage": "Garbage",
    "drainage": "Drainage",
    "streetlight": "Streetlight",
    "water_leakage": "Water leakage",
    "other": "Other",
}


class Command(BaseCommand):
    help = "Ensure the standard report categories exist without creating demo users or reports."

    def handle(self, *args, **options):
        created = 0
        for name, label in REPORT_CATEGORIES.items():
            _, was_created = Category.objects.get_or_create(
                name=name,
                defaults={
                    "label": label,
                    "is_active": True,
                    "default_due_hours": 72,
                },
            )
            created += was_created
        self.stdout.write(f"Ensured {len(REPORT_CATEGORIES)} standard report categories ({created} created).")

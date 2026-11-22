import secrets
from datetime import date

from django.contrib.gis.geos import MultiPolygon, Polygon

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.geography.models import Category, Department, RoutingRule, Ward
from django.utils import timezone

# Fixed local demo centre in Hyderabad, Telangana; this is not pilot geography.
DEMO_LATITUDE = 17.3850
DEMO_LONGITUDE = 78.4867

class Command(BaseCommand):
    help = "Create local demo accounts with random passwords (printed once)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing demo seed with DEBUG=False. Pass --force to continue.")
        lat, lon = DEMO_LATITUDE, DEMO_LONGITUDE
        # A synthetic central Hyderabad area keeps local demos in Telangana without claiming pilot boundaries.
        half_side = 0.1
        ring = ((lon-half_side, lat-half_side), (lon+half_side, lat-half_side), (lon+half_side, lat+half_side), (lon-half_side, lat+half_side), (lon-half_side, lat-half_side))
        ward, _ = Ward.objects.update_or_create(name="Demo Ward", defaults={"boundary": MultiPolygon(Polygon(ring), srid=4326), "source": f"synthetic demo boundary centered in Hyderabad, Telangana; not pilot data; {date.today().isoformat()}", "effective_from": date.today()})
        # All seeded categories share the staff department so one demo login set can exercise a full workflow.
        demo_department, _ = Department.objects.get_or_create(name="Demo Department — Roads")
        for name in ("Sanitation", "Water", "Lighting"):
            Department.objects.get_or_create(name=f"Demo Department — {name}")
        categories = ["pothole", "garbage", "drainage", "streetlight", "water_leakage", "other"]
        for category_name in categories:
            category, _ = Category.objects.update_or_create(
                name=category_name,
                defaults={"default_due_hours": 72, "default_department": demo_department},
            )
            RoutingRule.objects.update_or_create(
                category=category, ward=ward, version=1,
                defaults={"department": demo_department, "effective_from": timezone.now()},
            )
        roles = [
            User.Role.CITIZEN,
            User.Role.TRIAGE_REVIEWER,
            User.Role.DEPARTMENT_OFFICIAL,
            User.Role.SUPERVISOR,
            User.Role.FIELD_WORKER,
        ]
        for role in roles:
            email = f"{role}@example.test"
            password = secrets.token_urlsafe(24)
            defaults = {
                "name": f"Demo {role.replace('_', ' ').title()}",
                "role": role,
                "username": email,
            }
            if role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR, User.Role.FIELD_WORKER}:
                defaults["department"] = demo_department
            user, created = User.objects.get_or_create(email=email, defaults=defaults)
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
                self.stdout.write(f"{email} {password}")
            else:
                if role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR, User.Role.FIELD_WORKER} and user.department_id != demo_department.pk:
                    user.department = demo_department
                    user.save(update_fields=["department"])
                self.stdout.write(f"Skipped existing account: {email}")

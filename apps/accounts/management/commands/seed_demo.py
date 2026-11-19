import secrets
from datetime import date

from django.contrib.gis.geos import MultiPolygon, Polygon

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.geography.models import Category, Department, RoutingRule, Ward
from django.utils import timezone

class Command(BaseCommand):
    help = "Create local demo accounts with random passwords (printed once)."

    def add_arguments(self, parser):
        parser.add_argument("--lat", type=float, required=True)
        parser.add_argument("--lon", type=float, required=True)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing demo seed with DEBUG=False. Pass --force to continue.")
        lat, lon = options["lat"], options["lon"]
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise CommandError("Latitude or longitude is outside valid coordinate bounds.")
        # A small square gives local demos a supported area without inventing pilot geography.
        half_side = 0.001
        ring = ((lon-half_side, lat-half_side), (lon+half_side, lat-half_side), (lon+half_side, lat+half_side), (lon-half_side, lat+half_side), (lon-half_side, lat-half_side))
        ward, _ = Ward.objects.update_or_create(name="Demo Ward", defaults={"boundary": MultiPolygon(Polygon(ring), srid=4326), "source": f"hand-drawn, {date.today().isoformat()}", "effective_from": date.today()})
        departments = [Department.objects.get_or_create(name=f"Demo Department — {name}")[0] for name in ("Roads", "Sanitation", "Water", "Lighting")]
        categories = ["pothole", "garbage", "drainage", "streetlight", "water_leakage", "other"]
        for index, category_name in enumerate(categories):
            category, _ = Category.objects.get_or_create(name=category_name, defaults={"default_due_hours": 72, "default_department": departments[index % len(departments)]})
            department = category.default_department or departments[index % len(departments)]
            if category.default_department_id is None:
                category.default_department = department
                category.save(update_fields=["default_department"])
            RoutingRule.objects.get_or_create(category=category, ward=ward, version=1, defaults={"department": department, "effective_from": timezone.now()})
        roles = [
            User.Role.CITIZEN,
            User.Role.TRIAGE_REVIEWER,
            User.Role.DEPARTMENT_OFFICIAL,
            User.Role.SUPERVISOR,
            User.Role.FIELD_WORKER,
        ]
        department, _ = Department.objects.get_or_create(name="Demo Department")
        for role in roles:
            email = f"{role}@example.test"
            password = secrets.token_urlsafe(24)
            defaults = {
                "name": f"Demo {role.replace('_', ' ').title()}",
                "role": role,
                "username": email,
            }
            if role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR, User.Role.FIELD_WORKER}:
                defaults["department"] = department
            user, created = User.objects.get_or_create(email=email, defaults=defaults)
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
                self.stdout.write(f"{email} {password}")
            else:
                self.stdout.write(f"Skipped existing account: {email}")

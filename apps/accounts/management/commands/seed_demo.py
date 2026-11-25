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
DEMO_ACCOUNT_PHONES = {
    User.Role.CITIZEN: "+919876502201",
    User.Role.TRIAGE_REVIEWER: "+919876502202",
    User.Role.DEPARTMENT_OFFICIAL: "+919876502203",
    User.Role.FIELD_WORKER: "+919876502204",
    User.Role.SUPERVISOR: "+919876502205",
    User.Role.ADMIN: "+919876502206",
}

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
        categories = {
            "pothole": "Pothole",
            "garbage": "Garbage",
            "drainage": "Drainage",
            "streetlight": "Streetlight",
            "water_leakage": "Water leakage",
            "other": "Other",
        }
        for category_name, label in categories.items():
            category, _ = Category.objects.update_or_create(
                name=category_name,
                defaults={
                    "label": label,
                    "is_active": True,
                    "default_due_hours": 72,
                    "default_department": demo_department,
                },
            )
            RoutingRule.objects.update_or_create(
                category=category, ward=ward, version=1,
                defaults={"department": demo_department, "effective_from": timezone.now()},
            )
        roles = [
            User.Role.CITIZEN,
            User.Role.TRIAGE_REVIEWER,
            User.Role.DEPARTMENT_OFFICIAL,
            User.Role.FIELD_WORKER,
            User.Role.SUPERVISOR,
            User.Role.ADMIN,
        ]
        for role in roles:
            email = f"{role}@example.test"
            phone_number = DEMO_ACCOUNT_PHONES[role]
            password = secrets.token_urlsafe(24)
            defaults = {
                "name": f"Demo {role.replace('_', ' ').title()}",
                "role": role,
                "username": phone_number,
                "phone_number": phone_number,
                "email": email if role != User.Role.CITIZEN else None,
            }
            if role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR, User.Role.FIELD_WORKER}:
                defaults["department"] = demo_department
            if role == User.Role.ADMIN:
                defaults.update(is_staff=True, is_superuser=True)
            user = User.objects.filter(phone_number=phone_number).first()
            if user is None:
                # Migrate a previous email-only local demo seed in place when one exists.
                user = User.objects.filter(email=email).first()
            created = user is None
            if created:
                if role == User.Role.ADMIN:
                    user = User.objects.create_superuser(
                        phone_number=phone_number, password=password,
                        name=defaults["name"], email=None,
                    )
                else:
                    user = User.objects.create_user(
                        phone_number=phone_number, password=password,
                        name=defaults["name"], role=role,
                        email=defaults["email"],
                        department=defaults.get("department"),
                    )
            else:
                user.phone_number = phone_number
                user.username = phone_number
                user.email = defaults["email"]
                user.role = role
                user.name = defaults["name"]
                if role in {User.Role.DEPARTMENT_OFFICIAL, User.Role.SUPERVISOR, User.Role.FIELD_WORKER}:
                    user.department = demo_department
                if role == User.Role.ADMIN:
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
            if created:
                self.stdout.write(f"Created {role} login {phone_number}; password (shown once): {password}")
            else:
                self.stdout.write(f"Skipped existing demo account: {phone_number}")

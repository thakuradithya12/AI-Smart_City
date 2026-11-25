import secrets
from datetime import date, timedelta
from pathlib import Path

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.contrib.gis.geos import Point
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.complaints.models import Complaint, Evidence
from apps.complaints.services import delete_private_files, private_storage, store_citizen_image
from apps.geography.models import Category, Department, RoutingRule, Ward
from apps.workflow.services import transition

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
DEMO_COMPLAINTS = (
    {
        "public_id": "DEMO-REPORT-001",
        "category": "pothole",
        "description": "Synthetic sample report; image is an illustration, not a real street photo.",
        "photo": "demo-pothole.png",
        "longitude_offset": -0.01,
    },
    {
        "public_id": "DEMO-REPORT-002",
        "category": "streetlight",
        "description": "Synthetic sample report; image is an illustration, not a real street photo.",
        "photo": "demo-streetlight.png",
        "longitude_offset": 0.01,
    },
)

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
        users_by_role = {}
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
            users_by_role[role] = user

        self._seed_demo_complaints(users_by_role[User.Role.CITIZEN], ward, lat, lon)

    def _seed_demo_complaints(self, citizen, ward, latitude, longitude):
        for sample in DEMO_COMPLAINTS:
            complaint = Complaint.objects.visible_to(citizen).filter(
                public_id=sample["public_id"]
            ).first()
            if complaint is None:
                category = Category.objects.get(name=sample["category"])
                complaint = Complaint.objects.create(
                    public_id=sample["public_id"],
                    citizen=citizen,
                    category=category,
                    description=sample["description"],
                    location=Point(
                        longitude + sample["longitude_offset"], latitude, srid=4326
                    ),
                    ward=ward,
                    due_at=timezone.now() + timedelta(hours=category.default_due_hours),
                    consent_at=timezone.now(),
                    consent_version=settings.PRIVACY_NOTICE_VERSION,
                )
                AuditEvent.objects.create(
                    actor=citizen,
                    role=citizen.role,
                    action="demo_complaint_seeded",
                    object_type="Complaint",
                    object_id=str(complaint.pk),
                    after={"status": Complaint.Status.SUBMITTED},
                    reason="Synthetic local demo fixture; not a citizen-submitted report.",
                )
                transition(complaint, Complaint.Status.IN_TRIAGE, actor=None)
                self.stdout.write(f"Created sample complaint: {complaint.public_id}")

            self._ensure_sample_evidence(
                complaint, citizen, sample["photo"]
            )

    def _ensure_sample_evidence(self, complaint, citizen, filename):
        evidence = Evidence.objects.filter(
            complaint=complaint, kind=Evidence.Kind.CITIZEN
        ).order_by("pk").first()
        if evidence and all(
            private_storage.exists(path)
            for path in (evidence.original_path, evidence.display_path, evidence.thumbnail_path)
            if path
        ):
            return

        fixture_path = Path(settings.BASE_DIR) / "apps" / "complaints" / "fixtures" / filename
        with fixture_path.open("rb") as fixture_file:
            upload = SimpleUploadedFile(
                filename, fixture_file.read(), content_type="image/png"
            )
        original_path, display_path, thumbnail_path, image_hash = store_citizen_image(upload)
        if evidence:
            old_paths = [evidence.original_path, evidence.display_path, evidence.thumbnail_path]
            evidence.original_path = original_path
            evidence.display_path = display_path
            evidence.thumbnail_path = thumbnail_path
            evidence.sha256 = image_hash
            evidence.uploaded_by = citizen
            evidence.save(update_fields=[
                "original_path", "display_path", "thumbnail_path", "sha256", "uploaded_by"
            ])
            delete_private_files(old_paths)
        else:
            Evidence.objects.create(
                complaint=complaint,
                kind=Evidence.Kind.CITIZEN,
                original_path=original_path,
                display_path=display_path,
                thumbnail_path=thumbnail_path,
                sha256=image_hash,
                uploaded_by=citizen,
            )

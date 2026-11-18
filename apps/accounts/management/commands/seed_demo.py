import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.geography.models import Department

class Command(BaseCommand):
    help = "Create local demo accounts with random passwords (printed once)."

    def handle(self, *args, **options):
        if not settings.DEBUG and not getattr(settings, "ALLOW_DEMO_SEED", False):
            raise CommandError("Demo accounts are disabled outside development/demo settings.")
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

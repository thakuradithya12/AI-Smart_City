from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.phone_numbers import normalize_phone_number


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number=None, password=None, email=None, **extra_fields):
        normalized_phone = None
        normalized_email = None
        if phone_number:
            try:
                normalized_phone = normalize_phone_number(phone_number)
            except ValidationError as exc:
                raise ValueError("A valid Indian mobile number is required") from exc
        elif email:
            # Keep previously provisioned staff and fixtures usable during phone migration.
            normalized_email = self.normalize_email(email)
        else:
            raise ValueError("A phone number is required")
        extra_fields.setdefault("username", normalized_phone or normalized_email)
        user = self.model(phone_number=normalized_phone, email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number=None, password=None, email=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, email=email, **extra_fields)

    def create_superuser(self, phone_number=None, password=None, email=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self._create_user(phone_number, password, email=email, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        TRIAGE_REVIEWER = "triage_reviewer", "Triage reviewer"
        DEPARTMENT_OFFICIAL = "department_official", "Department official"
        SUPERVISOR = "supervisor", "Supervisor"
        FIELD_WORKER = "field_worker", "Field worker"
        ADMIN = "admin", "Admin"

    # Emails remain optional only to preserve already provisioned staff accounts during migration.
    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=13, unique=True, blank=True, null=True)
    name = models.CharField(max_length=160)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.CITIZEN)
    department = models.ForeignKey("geography.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="users")
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    def __str__(self):
        return self.name or self.phone_number or self.email or str(self.pk)

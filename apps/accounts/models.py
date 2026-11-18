from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        user = self.model(email=self.normalize_email(email), username=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        TRIAGE_REVIEWER = "triage_reviewer", "Triage reviewer"
        DEPARTMENT_OFFICIAL = "department_official", "Department official"
        SUPERVISOR = "supervisor", "Supervisor"
        FIELD_WORKER = "field_worker", "Field worker"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=160)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.CITIZEN)
    department = models.ForeignKey("geography.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="users")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    def __str__(self):
        return self.name or self.email

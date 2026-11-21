from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class WardQuerySet(models.QuerySet):
    def active_on(self, day=None):
        effective_day = day or timezone.localdate()
        # Ward boundaries are eligible only within their recorded effective-date window.
        return self.filter(effective_from__lte=effective_day).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=effective_day)
        )


class Ward(models.Model):
    objects = models.Manager.from_queryset(WardQuerySet)()

    name = models.CharField(max_length=120, unique=True)
    boundary = models.MultiPolygonField(srid=4326)
    source = models.CharField(max_length=240)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(effective_to__isnull=True) | Q(effective_to__gte=F("effective_from")),
                name="ward_effective_window_valid",
            )
        ]

    def clean(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError({"effective_to": "End date must be on or after the start date."})

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    default_due_hours = models.PositiveIntegerField(default=72)
    default_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)
    is_safety_critical = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class RoutingRule(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    ward = models.ForeignKey(Ward, null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    effective_from = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["category", "ward", "version"], name="unique_routing_rule_version")]

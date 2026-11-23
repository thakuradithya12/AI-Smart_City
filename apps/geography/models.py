from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.utils import timezone

from apps.geography.geometry import has_area_overlap, validated_multi_polygon

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
        errors = {}
        if self.effective_to and self.effective_to < self.effective_from:
            errors["effective_to"] = "End date must be on or after the start date."
        if self.boundary is not None:
            try:
                self.boundary = validated_multi_polygon(self.boundary)
            except ValidationError as exc:
                errors["boundary"] = exc.messages
        if errors:
            raise ValidationError(errors)
        if self.boundary is None:
            return
        # Ward records may overlap in time only when their polygon interiors do not overlap.
        candidates = Ward.objects.filter(boundary__intersects=self.boundary).exclude(pk=self.pk)
        if self.effective_to:
            candidates = candidates.filter(effective_from__lte=self.effective_to)
        candidates = candidates.filter(Q(effective_to__isnull=True) | Q(effective_to__gte=self.effective_from))
        for ward in candidates.iterator():
            if has_area_overlap(self.boundary, ward.boundary):
                raise ValidationError({"boundary": f"Ward boundary overlaps active ward '{ward.name}'."})

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=100, blank=True, default="")
    icon = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    default_due_hours = models.PositiveIntegerField(default=72)
    default_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)
    is_safety_critical = models.BooleanField(default=False)

    @property
    def display_label(self):
        return self.label.strip() or self.name.replace("_", " ").title()

    def __str__(self):
        return self.display_label

class RoutingRule(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    ward = models.ForeignKey(Ward, null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    effective_from = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["category", "ward", "version"], name="unique_routing_rule_version")]

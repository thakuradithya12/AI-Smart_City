from django.contrib.gis.db import models

class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Ward(models.Model):
    name = models.CharField(max_length=120, unique=True)
    boundary = models.MultiPolygonField(srid=4326)
    source = models.CharField(max_length=240)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

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

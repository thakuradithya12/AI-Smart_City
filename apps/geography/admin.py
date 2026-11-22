from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Category, Department, RoutingRule, Ward


@admin.register(Ward)
class WardAdmin(GISModelAdmin):
    list_display = ("name", "source", "effective_from", "effective_to")
    list_filter = ("effective_from", "effective_to")
    search_fields = ("name", "source")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "default_due_hours", "default_department", "is_safety_critical")
    list_filter = ("is_safety_critical", "default_department")
    search_fields = ("name",)


@admin.register(RoutingRule)
class RoutingRuleAdmin(admin.ModelAdmin):
    list_display = ("category", "ward", "department", "version", "effective_from")
    list_filter = ("category", "ward", "department", "effective_from")
    search_fields = ("category__name", "department__name", "ward__name")

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import path
from django.utils import timezone

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
    change_list_template = "admin/geography/category/change_list.html"
    list_display = ("label", "name", "is_active", "icon", "default_due_hours", "default_department", "is_safety_critical")
    list_filter = ("is_active", "is_safety_critical", "default_department")
    search_fields = ("name", "label")

    def get_urls(self):
        custom_urls = [
            path(
                "routing-gaps/",
                self.admin_site.admin_view(self.routing_gaps),
                name="geography_category_routing_gaps",
            )
        ]
        return custom_urls + super().get_urls()

    def routing_gaps(self, request):
        if request.user.role != "admin" and not request.user.is_superuser:
            raise PermissionDenied
        ward_id = request.GET.get("ward", "")
        ward = get_object_or_404(Ward, pk=ward_id) if ward_id.isdecimal() else None
        missing_categories = Category.objects.none()
        if ward:
            covered_category_ids = RoutingRule.objects.filter(
                effective_from__lte=timezone.now(),
            ).filter(
                Q(ward=ward) | Q(ward__isnull=True)
            ).values_list("category_id", flat=True)
            missing_categories = Category.objects.filter(is_active=True).exclude(
                pk__in=covered_category_ids
            ).order_by("label", "name")
        return render(request, "admin/geography/category/routing_gaps.html", {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Categories without an active routing rule",
            "wards": Ward.objects.order_by("name"),
            "selected_ward": ward,
            "missing_categories": missing_categories,
        })


@admin.register(RoutingRule)
class RoutingRuleAdmin(admin.ModelAdmin):
    list_display = ("category", "ward", "department", "version", "effective_from")
    list_filter = ("category", "ward", "department", "effective_from")
    search_fields = ("category__name", "department__name", "ward__name")

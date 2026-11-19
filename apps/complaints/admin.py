from django.contrib import admin

from .models import Complaint, ComplaintMessage, Evidence, Resolution, StatusEvent


class WorkflowReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Complaint)
class ComplaintAdmin(WorkflowReadOnlyAdmin):
    list_display = ("public_id", "status", "category", "ward", "department", "assignee", "due_at", "created_at")
    list_filter = ("status", "category", "ward", "department")
    search_fields = ("public_id", "description", "citizen__name")
    readonly_fields = tuple(field.name for field in Complaint._meta.fields)

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff


@admin.register(ComplaintMessage)
class ComplaintMessageAdmin(WorkflowReadOnlyAdmin):
    list_display = ("complaint", "author", "created_at")
    search_fields = ("complaint__public_id", "body", "author__name")
    readonly_fields = tuple(field.name for field in ComplaintMessage._meta.fields)


@admin.register(Evidence)
class EvidenceAdmin(WorkflowReadOnlyAdmin):
    list_display = ("complaint", "kind", "uploaded_by", "uploaded_at", "sha256")
    list_filter = ("kind", "uploaded_at")
    search_fields = ("complaint__public_id", "sha256")
    readonly_fields = tuple(field.name for field in Evidence._meta.fields)


@admin.register(Resolution)
class ResolutionAdmin(WorkflowReadOnlyAdmin):
    list_display = ("complaint", "claimed_by", "claimed_at", "verified_by", "verified_at", "outcome")
    readonly_fields = tuple(field.name for field in Resolution._meta.fields)


@admin.register(StatusEvent)
class StatusEventAdmin(WorkflowReadOnlyAdmin):
    list_display = ("complaint", "from_status", "to_status", "actor", "role", "created_at")
    list_filter = ("to_status", "role", "created_at")
    readonly_fields = tuple(field.name for field in StatusEvent._meta.fields)

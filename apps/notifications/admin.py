from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "event", "complaint", "created_at", "read_at", "sent_at", "attempts")
    list_filter = ("event", "created_at", "sent_at")
    search_fields = ("recipient__name", "complaint__public_id")
    readonly_fields = tuple(field.name for field in Notification._meta.fields)

from apps.notifications.models import Notification


def notification_badge(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or not user.is_active:
        return {"notification_unread_count": 0}
    return {
        "notification_unread_count": Notification.objects.for_user(user).filter(read_at__isnull=True).count()
    }

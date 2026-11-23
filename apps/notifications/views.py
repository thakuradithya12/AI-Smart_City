from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.notifications.models import Notification


@login_required
def inbox(request):
    notifications = Notification.objects.for_user(request.user).select_related("complaint")
    return render(request, "notifications/inbox.html", {
        "notifications": notifications[:100],
        "unread_count": notifications.filter(read_at__isnull=True).count(),
    })


@login_required
def mark_read(request, pk):
    if request.method != "POST":
        raise Http404
    notification = get_object_or_404(Notification.objects.for_user(request.user), pk=pk)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("notifications_inbox")

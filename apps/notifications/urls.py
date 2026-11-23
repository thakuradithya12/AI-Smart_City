from django.urls import path

from apps.notifications import views


urlpatterns = [
    path("notifications/", views.inbox, name="notifications_inbox"),
    path("notifications/<int:pk>/read/", views.mark_read, name="notification_mark_read"),
]

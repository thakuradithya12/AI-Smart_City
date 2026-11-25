from django.urls import path

from . import views


urlpatterns = [
    path("privacy/", views.privacy_notice, name="privacy_notice"),
    path("privacy/export/", views.export_my_data, name="privacy_export"),
    path("privacy/delete-request/", views.request_account_deletion, name="privacy_delete_request"),
]

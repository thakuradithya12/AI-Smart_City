from django.contrib import admin
from django.urls import include, path
from apps.accounts.views import WorkspaceLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", WorkspaceLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.console.urls")),
]

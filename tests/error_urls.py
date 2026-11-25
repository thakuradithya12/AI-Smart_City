from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.urls import path
from django.views import defaults
from django.http import HttpResponse


def home(request):
    return HttpResponse("Test home")


def bad_request_trigger(request):
    raise SuspiciousOperation("test bad request")


def forbidden_trigger(request):
    raise PermissionDenied


def server_error_trigger(request):
    raise RuntimeError("test server error")


urlpatterns = [
    path("", home, name="home"),
    path("400/", bad_request_trigger),
    path("403/", forbidden_trigger),
    path("500/", server_error_trigger),
]

handler400 = defaults.bad_request
handler403 = defaults.permission_denied
handler404 = defaults.page_not_found
handler500 = defaults.server_error

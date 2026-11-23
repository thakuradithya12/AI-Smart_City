import os

from .base import *  # noqa: F403
from django.core.exceptions import ImproperlyConfigured
from . import base as base_settings

DEBUG = False
CSP_REPORT_ONLY = os.environ.get("CSP_REPORT_ONLY", "False").lower() == "true"
if not base_settings.SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 300
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Axes counts failed logins; the rolling window prevents a burst from blocking a user for longer than needed.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_USE_ATTEMPT_EXPIRATION = True
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_CLIENT_IP_CALLABLE = "config.settings.prod.get_client_ip"


def get_client_ip(request):
    # Caddy overwrites untrusted X-Forwarded-For values before forwarding to Django.
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded_for.split(",", 1)[0].strip() or request.META.get("REMOTE_ADDR")

# PostgreSQL shares this limiter across web processes.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}
REPORT_POST_LIMIT = int(os.environ.get("REPORT_POST_LIMIT", "5"))
REPORT_POST_WINDOW_SECONDS = int(os.environ.get("REPORT_POST_WINDOW_SECONDS", "3600"))

# Production email delivery is configured only from environment-provided SMTP settings.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@localhost")

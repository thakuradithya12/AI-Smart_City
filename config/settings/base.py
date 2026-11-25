import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from config.database import database_config_from_url

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.environ.get("SECRET_KEY", os.environ.get("DJANGO_SECRET_KEY", ""))
DEBUG = os.environ.get("DEBUG", os.environ.get("DJANGO_DEBUG", "False")).lower() in {
    "1", "true", "yes", "on",
}
ALLOWED_HOSTS = [
    host for host in os.environ.get(
        "ALLOWED_HOSTS", os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
    ).split(",") if host
]
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS", os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
    ).split(",") if origin
]
# Cross-origin tile requests require the site origin in Referer; never send full paths externally.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "django.contrib.gis", "axes", "apps.accounts", "apps.geography", "apps.complaints",
    "apps.notifications",
    "apps.scheduler",
    "apps.workflow", "apps.audit", "apps.console", "apps.ai_assist",
]
MIDDLEWARE = [
    "config.middleware.RequestIdMiddleware",
    "django.middleware.security.SecurityMiddleware", "config.middleware.BrowserPolicyHeadersMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages", "apps.notifications.context_processors.notification_badge"]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    try:
        default_database = database_config_from_url(DATABASE_URL)
    except ValueError as exc:
        raise ImproperlyConfigured(str(exc)) from exc
else:
    default_database = {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "smart_city"),
        "USER": os.environ.get("POSTGRES_USER", "smart_city"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
DATABASES = {"default": default_database}
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["axes.backends.AxesStandaloneBackend", "apps.accounts.backends.PhoneOrLegacyEmailBackend"]
AXES_USERNAME_CALLABLE = "apps.accounts.backends.axes_username"
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
MEDIA_ROOT = BASE_DIR / "private_media"
MEDIA_URL = None
EVIDENCE_DISPLAY_MAX_EDGE = int(os.environ.get("EVIDENCE_DISPLAY_MAX_EDGE", "1600"))
REPORT_MAX_PHOTOS = int(os.environ.get("REPORT_MAX_PHOTOS", "3"))
LIST_PAGE_SIZE = int(os.environ.get("LIST_PAGE_SIZE", "20"))
MAP_TILE_URL = os.environ.get(
    "MAP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
)
_csp_report_only_env = os.environ.get("CSP_REPORT_ONLY", "").strip()
CSP_REPORT_ONLY = _csp_report_only_env.lower() == "true" if _csp_report_only_env else True
# Retention settings use whole-day cutoffs; month-based defaults use 30/365-day approximations.
COMPLAINT_RETENTION_DAYS = int(os.environ.get("COMPLAINT_RETENTION_DAYS", "365"))
CLOSED_PHOTO_RETENTION_DAYS = int(os.environ.get("CLOSED_PHOTO_RETENTION_DAYS", "365"))
REJECTED_CANCELLED_RETENTION_DAYS = int(os.environ.get("REJECTED_CANCELLED_RETENTION_DAYS", "183"))
INACTIVE_ACCOUNT_RETENTION_DAYS = int(os.environ.get("INACTIVE_ACCOUNT_RETENTION_DAYS", "730"))
DELETION_REQUEST_DAYS = int(os.environ.get("DELETION_REQUEST_DAYS", "30"))
PRIVACY_NOTICE_VERSION = os.environ.get("PRIVACY_NOTICE_VERSION", "2026-11-25-v1")
CITIZEN_REMINDER_DAYS = int(os.environ.get("CITIZEN_REMINDER_DAYS", "3"))
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "http://localhost:8000")
NOTIFICATION_BATCH_SIZE = int(os.environ.get("NOTIFICATION_BATCH_SIZE", "100"))
NOTIFICATION_MAX_ATTEMPTS = int(os.environ.get("NOTIFICATION_MAX_ATTEMPTS", "3"))
NOTIFICATION_RETRY_DELAYS_SECONDS = (60, 300, 1800)
NOTIFICATION_SEND_LEASE_SECONDS = 600
SCHEDULER_POLL_SECONDS = int(os.environ.get("SCHEDULER_POLL_SECONDS", "15"))
SCHEDULER_HEARTBEAT_STALE_SECONDS = int(os.environ.get("SCHEDULER_HEARTBEAT_STALE_SECONDS", "180"))
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 43200
SESSION_SAVE_EVERY_REQUEST = True
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "config.logging.JsonLogFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        },
    },
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@localhost")

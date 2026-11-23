import json
import os
import subprocess
import sys
import uuid
from logging import INFO, LogRecord

import pytest
from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from config.logging import JsonLogFormatter, request_id_var
from config.middleware import BrowserPolicyHeadersMiddleware, RequestIdMiddleware


@pytest.mark.django_db
def test_healthz_is_public_and_checks_the_database(client):
    response = client.get("/healthz/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scheduler": "unknown"}
    assert response["Cache-Control"] == "no-store"
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_healthz_returns_generic_unavailable_response_when_database_fails(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OperationalError("database disconnected")

    monkeypatch.setattr("config.views.connection.cursor", unavailable)
    response = client.get("/healthz/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert b"database disconnected" not in response.content


def test_request_id_is_generated_and_returned_on_response():
    middleware = RequestIdMiddleware(lambda request: HttpResponse("ok"))
    response = middleware(RequestFactory().get("/healthz/"))
    request_id = response["X-Request-ID"]
    assert uuid.UUID(hex=request_id).hex == request_id


def test_json_log_formatter_includes_request_id_and_no_exception_text():
    token = request_id_var.set("a" * 32)
    try:
        record = LogRecord("apps.health", INFO, "", 0, "database check failed", (), None)
        formatted = json.loads(JsonLogFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert formatted["request_id"] == "a" * 32
    assert formatted["message"] == "database check failed"
    assert "exception" not in formatted


def test_explicit_same_site_cookie_policy(settings):
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.CSRF_COOKIE_SAMESITE == "Lax"


def test_idle_session_timeout_uses_rolling_twelve_hour_window(settings):
    assert settings.SESSION_COOKIE_AGE == 43200
    assert settings.SESSION_SAVE_EVERY_REQUEST is True


def test_owner_retention_defaults_are_configurable(settings):
    assert settings.COMPLAINT_RETENTION_DAYS == 365
    assert settings.CLOSED_PHOTO_RETENTION_DAYS == 365
    assert settings.REJECTED_CANCELLED_RETENTION_DAYS == 183
    assert settings.INACTIVE_ACCOUNT_RETENTION_DAYS == 730
    assert settings.DELETION_REQUEST_DAYS == 30


@override_settings(CSP_REPORT_ONLY=True)
def test_browser_policy_sets_report_only_csp_header():
    middleware = BrowserPolicyHeadersMiddleware(lambda request: HttpResponse("ok"))
    response = middleware(RequestFactory().get("/"))

    assert "Content-Security-Policy" not in response
    assert response["Content-Security-Policy-Report-Only"] == (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data: https://tile.openstreetmap.org; "
        "font-src 'self'; connect-src 'self'; object-src 'none'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )


def test_development_defaults_to_csp_report_only(settings):
    assert settings.CSP_REPORT_ONLY is True


@override_settings(CSP_REPORT_ONLY=False)
def test_browser_policy_enforces_csp_by_default_when_configured():
    middleware = BrowserPolicyHeadersMiddleware(lambda request: HttpResponse("ok"))
    response = middleware(RequestFactory().get("/"))

    assert "Content-Security-Policy-Report-Only" not in response
    assert "img-src 'self' data: https://tile.openstreetmap.org" in response["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]


def test_production_settings_force_debug_off_even_when_environment_requests_it():
    environment = os.environ.copy()
    environment.update({
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": "test-only-production-settings-key",
        "DJANGO_DEBUG": "True",
    })
    result = subprocess.run(
        [sys.executable, "-c", "from django.conf import settings; print(settings.DEBUG)"],
        env=environment, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == "False"


def test_production_settings_enforce_csp_by_default():
    environment = os.environ.copy()
    environment.update({
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": "test-only-production-settings-key",
    })
    environment.pop("CSP_REPORT_ONLY", None)
    result = subprocess.run(
        [sys.executable, "-c", "from django.conf import settings; print(settings.CSP_REPORT_ONLY)"],
        env=environment, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == "False"


def test_production_email_backend_is_environment_smtp():
    environment = os.environ.copy()
    environment.update({
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": "test-only-production-settings-key",
    })
    result = subprocess.run(
        [sys.executable, "-c", "from django.conf import settings; print(settings.EMAIL_BACKEND)"],
        env=environment, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == "django.core.mail.backends.smtp.EmailBackend"

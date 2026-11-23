import json
import os
import subprocess
import sys
import uuid
from logging import INFO, LogRecord

import pytest
from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory

from config.logging import JsonLogFormatter, request_id_var
from config.middleware import RequestIdMiddleware


@pytest.mark.django_db
def test_healthz_is_public_and_checks_the_database(client):
    response = client.get("/healthz/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
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

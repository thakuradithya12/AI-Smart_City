from pathlib import Path

import pytest
from django.test import override_settings


@pytest.mark.parametrize(
    ("path", "status", "heading"),
    [
        ("/400/", 400, "Request not accepted"),
        ("/403/", 403, "You cannot access this page"),
        ("/missing/", 404, "Page not found"),
        ("/500/", 500, "Something went wrong"),
    ],
)
@override_settings(
    DEBUG=False,
    ALLOWED_HOSTS=["testserver", "localhost"],
    ROOT_URLCONF="tests.error_urls",
)
def test_custom_error_templates_render(client, path, status, heading):
    client.raise_request_exception = False

    response = client.get(path)

    assert response.status_code == status
    assert heading.encode() in response.content
    assert f"{status}.html" in [template.name for template in response.templates]


@pytest.mark.django_db
def test_public_landing_uses_template_and_archive_files_are_not_routed(client, settings, tmp_path):
    settings.BASE_DIR = tmp_path

    response = client.get("/")

    assert response.status_code == 200
    assert b"Recent local reports" in response.content
    assert client.get("/ui-showcase/").status_code == 404


@pytest.mark.django_db
def test_landing_uses_real_actions_public_updates_and_no_external_origins(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AI Smart City" in response.content
    assert b"Report an issue" in response.content
    assert b"Sign in" in response.content
    assert b"Recent local reports" in response.content
    assert b"https://" not in response.content
    assert b"http://" not in response.content


def test_runtime_templates_and_scripts_have_no_external_asset_cdn_references():
    project_root = Path(__file__).resolve().parents[1]
    candidates = [*project_root.joinpath("templates").rglob("*.html")]
    candidates.extend(
        path for path in project_root.joinpath("static").rglob("*")
        if path.is_file() and path.suffix in {".html", ".js", ".css"}
        and "vendor" not in path.parts
    )
    external_markers = ("cdn.", "unpkg", "googleapis", "tailwind")
    assert all(
        not any(marker in path.read_text(encoding="utf-8", errors="ignore").lower() for marker in external_markers)
        for path in candidates
    )


@pytest.mark.django_db
def test_base_uses_local_design_system_without_bootstrap(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"vendor/bootstrap/bootstrap.min.css" not in response.content
    project_root = Path(__file__).resolve().parents[1]
    stylesheet = project_root / "static" / "css" / "site.css"
    css = stylesheet.read_text(encoding="utf-8")
    for token in ("--color-evergreen:", "--space-4:", "--radius-card:", "--type-body:"):
        assert token in css
    assert "system-ui" in css


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_ui_showcase_is_not_routed_in_production(client):
    assert client.get("/ui-showcase/").status_code == 404

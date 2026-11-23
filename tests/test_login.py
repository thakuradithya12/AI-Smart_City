import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert b"Sign in" in response.content
    assert b"type=\"tel\"" in response.content
    assert response["Permissions-Policy"] == "camera=(), microphone=(), geolocation=(self)"
    assert response["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response["Cache-Control"] == "no-store"

@pytest.mark.django_db
def test_public_home_renders_landing_page(client):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert b"AI Smart City" in response.content

@pytest.mark.django_db
def test_workspace_requires_login(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302
    assert reverse("login") in response.url

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

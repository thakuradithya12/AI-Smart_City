import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core import mail
from django.test import override_settings
from django.test import RequestFactory
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.test import override_settings

@pytest.mark.django_db
def test_user_can_authenticate_with_normalized_phone_number():
    user_model = get_user_model()
    user_model.objects.create_user(phone_number="(987) 654-3210", password="long-test-password", name="Test Citizen")
    request = RequestFactory().post("/accounts/login/")
    user = authenticate(request=request, username="+91 98765 43210", password="long-test-password")
    assert user is not None
    assert user.name == "Test Citizen"


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.test",
)
def test_legacy_staff_password_reset_is_templated_and_sends_email(client):
    User = get_user_model()
    User.objects.create_user(
        email="staff-reset@example.test",
        password="Existing!Password987",
        name="Legacy Staff",
        role=User.Role.TRIAGE_REVIEWER,
    )

    page = client.get(reverse("password_reset"))
    assert page.status_code == 200
    assert "registration/password_reset_form.html" in [template.name for template in page.templates]

    response = client.post(reverse("password_reset"), {"email": "staff-reset@example.test"})
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "reset" in mail.outbox[0].subject.casefold()
    assert "/accounts/reset/" in mail.outbox[0].body


@pytest.mark.django_db
def test_legacy_email_accounts_are_normalized_and_unique_case_insensitively():
    User = get_user_model()
    first = User.objects.create_user(
        email="Staff.Case@example.test",
        password="Existing!Password987",
        name="Legacy Staff",
        role=User.Role.TRIAGE_REVIEWER,
    )
    assert first.email == "staff.case@example.test"
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email="STAFF.CASE@EXAMPLE.TEST",
            password="Existing!Password987",
            name="Duplicate Legacy Staff",
            role=User.Role.SUPERVISOR,
        )


@pytest.mark.django_db
@pytest.mark.parametrize("identifier", ["User@Example.com", "user@example.com", "USER@EXAMPLE.COM"])
def test_legacy_email_login_is_case_insensitive(identifier):
    User = get_user_model()
    User.objects.create_user(email="User@Example.com", password="Existing!Password987", name="Legacy")
    user = authenticate(request=RequestFactory().post("/accounts/login/"), username=identifier, password="Existing!Password987")
    assert user is not None


@pytest.mark.django_db
def test_phone_registration_duplicate_format_is_a_friendly_form_error(client):
    User = get_user_model()
    User.objects.create_user(phone_number="9876543210", password="Existing!Password987", name="Existing")
    response = client.post(reverse("register"), {"phone_number": "+91 98765 43210", "name": "Duplicate", "password1": "Strong!Password987", "password2": "Strong!Password987"})
    assert response.status_code == 200
    assert b"already uses this phone number" in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("identifier", ["123", "+91 12345", "abcdefghij"])
def test_phone_registration_rejects_invalid_number(client, identifier):
    response = client.post(reverse("register"), {"phone_number": identifier, "name": "Invalid", "password1": "Strong!Password987", "password2": "Strong!Password987"})
    assert response.status_code == 200
    assert b"Enter a valid Indian mobile number" in response.content


@pytest.mark.django_db
@override_settings(AXES_FAILURE_LIMIT=5, AXES_LOCKOUT_PARAMETERS=[["username", "ip_address"]], AXES_COOLOFF_TIME=1)
def test_axes_locks_phone_spellings_as_one_identifier(client):
    User = get_user_model()
    User.objects.create_user(phone_number="9876543210", password="Correct!Password987", name="Citizen")
    for identifier in ["+91 98765 43210", "09876543210", "9876543210", "+91-98765-43210", " 9876543210 "]:
        client.post(reverse("login"), {"username": identifier, "password": "wrong"})
    response = client.post(reverse("login"), {"username": "+91 98765 43210", "password": "Correct!Password987"})
    assert response.status_code != 302


@pytest.mark.django_db
@override_settings(AXES_FAILURE_LIMIT=5, AXES_LOCKOUT_PARAMETERS=[["username", "ip_address"]], AXES_COOLOFF_TIME=1)
def test_axes_locks_legacy_email_case_variants_as_one_identifier(client):
    User = get_user_model()
    User.objects.create_user(email="staff@example.test", password="Correct!Password987", name="Legacy")
    for identifier in ["staff@example.test", "STAFF@EXAMPLE.TEST", " Staff@Example.Test ", "Staff@example.test", "sTaFf@eXaMpLe.TeSt"]:
        client.post(reverse("login"), {"username": identifier, "password": "wrong"})
    response = client.post(reverse("login"), {"username": "STAFF@EXAMPLE.TEST", "password": "Correct!Password987"})
    assert response.status_code != 302

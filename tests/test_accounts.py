import pytest
from django.contrib.auth import authenticate, get_user_model

@pytest.mark.django_db
def test_user_can_authenticate_with_email():
    user_model = get_user_model()
    user_model.objects.create_user(email="citizen@example.test", password="long-test-password", name="Test Citizen")
    user = authenticate(username="citizen@example.test", password="long-test-password")
    assert user is not None
    assert user.name == "Test Citizen"

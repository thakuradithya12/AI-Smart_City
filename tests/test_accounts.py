import pytest
from django.contrib.auth import authenticate, get_user_model
from django.test import RequestFactory

@pytest.mark.django_db
def test_user_can_authenticate_with_normalized_phone_number():
    user_model = get_user_model()
    user_model.objects.create_user(phone_number="(987) 654-3210", password="long-test-password", name="Test Citizen")
    request = RequestFactory().post("/accounts/login/")
    user = authenticate(request=request, username="+91 98765 43210", password="long-test-password")
    assert user is not None
    assert user.name == "Test Citizen"

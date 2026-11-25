import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.accounts.management.commands.seed_demo import DEMO_ACCOUNT_PHONES
from apps.accounts.models import User


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_demo_creates_phone_accounts_and_is_safe_to_rerun(capsys):
    call_command("seed_demo")

    for role, phone_number in DEMO_ACCOUNT_PHONES.items():
        user = User.objects.get(phone_number=phone_number)
        assert user.role == role
        if role == User.Role.CITIZEN:
            assert user.email is None
        if role == User.Role.ADMIN:
            assert user.is_staff and user.is_superuser

    first_output = capsys.readouterr().out
    assert all(phone_number in first_output for phone_number in DEMO_ACCOUNT_PHONES.values())
    assert "password (shown once)" in first_output

    call_command("seed_demo")

    assert User.objects.filter(phone_number__in=DEMO_ACCOUNT_PHONES.values()).count() == len(
        DEMO_ACCOUNT_PHONES
    )
    assert "Skipped existing demo account" in capsys.readouterr().out

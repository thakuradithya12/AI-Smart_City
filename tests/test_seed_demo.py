import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.accounts.management.commands.seed_demo import DEMO_ACCOUNT_PHONES, DEMO_COMPLAINTS
from apps.accounts.models import User
from apps.complaints.models import Complaint, Evidence
from apps.complaints.services import private_storage


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

    citizen = User.objects.get(phone_number=DEMO_ACCOUNT_PHONES[User.Role.CITIZEN])
    complaints = list(
        Complaint.objects.visible_to(citizen).filter(
            public_id__in=[sample["public_id"] for sample in DEMO_COMPLAINTS]
        )
    )
    assert len(complaints) == len(DEMO_COMPLAINTS)
    assert all(complaint.status == Complaint.Status.IN_TRIAGE for complaint in complaints)
    evidence_rows = list(Evidence.objects.filter(complaint__in=complaints))
    assert len(evidence_rows) == len(DEMO_COMPLAINTS)
    assert all(private_storage.exists(item.original_path) for item in evidence_rows)

    for evidence in evidence_rows:
        for path in (evidence.original_path, evidence.display_path, evidence.thumbnail_path):
            if path:
                private_storage.delete(path)

    call_command("seed_demo")

    repaired_rows = list(Evidence.objects.filter(complaint__in=complaints))
    assert all(private_storage.exists(item.original_path) for item in repaired_rows)
    for evidence in repaired_rows:
        for path in (evidence.original_path, evidence.display_path, evidence.thumbnail_path):
            if path:
                private_storage.delete(path)

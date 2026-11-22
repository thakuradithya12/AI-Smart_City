from collections import defaultdict

from django.db import migrations, models
from django.db.models.functions import Lower


def normalize_existing_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    alias = schema_editor.connection.alias
    groups = defaultdict(list)
    for user_id, email in User.objects.using(alias).exclude(email__isnull=True).values_list("pk", "email"):
        groups[email.strip().lower()].append(user_id)

    # Never guess which existing staff account to keep; abort before modifying any user rows.
    collisions = sum(1 for user_ids in groups.values() if len(user_ids) > 1)
    if collisions:
        raise RuntimeError(
            f"Cannot normalize legacy emails: {collisions} case-insensitive duplicate groups need owner review. "
            "No accounts were changed. Resolve those accounts before retrying this migration."
        )

    updates = []
    for user_id, email in User.objects.using(alias).exclude(email__isnull=True).values_list("pk", "email"):
        normalized = email.strip().lower()
        if email != normalized:
            updates.append(User(pk=user_id, email=normalized))
    if updates:
        User.objects.using(alias).bulk_update(updates, ["email"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_phone_number_alter_user_email")]

    operations = [
        migrations.RunPython(normalize_existing_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"), name="user_email_case_insensitive_unique"
            ),
        ),
    ]

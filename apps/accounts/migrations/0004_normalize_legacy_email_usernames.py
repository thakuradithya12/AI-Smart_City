from django.db import migrations


def normalize_email_usernames(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    alias = schema_editor.connection.alias
    rows = User.objects.using(alias).exclude(email__isnull=True).values_list("pk", "username", "email")
    updates = [
        User(pk=user_id, username=email.strip().lower())
        for user_id, username, email in rows
        if username and username.strip().casefold() == email.strip().casefold()
    ]
    if updates:
        User.objects.using(alias).bulk_update(updates, ["username"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_user_email_case_insensitive_unique")]
    operations = [migrations.RunPython(normalize_email_usernames, migrations.RunPython.noop)]

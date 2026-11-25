import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_alter_user_options")]

    operations = [
        migrations.CreateModel(
            name="PrivacyDeletionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requested_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="privacy_deletion_requests", to="accounts.user")),
            ],
        ),
        migrations.AddIndex(
            model_name="privacydeletionrequest",
            index=models.Index(fields=["processed_at", "requested_at"], name="privacy_delete_pending_idx"),
        ),
    ]

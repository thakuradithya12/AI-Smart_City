import django.conf
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("complaints", "0005_complaint_landmark"),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(choices=[
                    ("report_received", "Report received"),
                    ("information_requested", "More information requested"),
                    ("routed", "Assigned to a department"),
                    ("work_claimed", "Work marked complete"),
                    ("verified_closed", "Complaint verified and closed"),
                    ("reopened", "Complaint reopened"),
                    ("assigned_to_me", "Work assigned to you"),
                    ("overdue", "Complaint overdue"),
                    ("citizen_reminder", "Please review the work update"),
                ], max_length=32)),
                ("status", models.CharField(max_length=40)),
                ("event_key", models.CharField(max_length=200, unique=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("email_skipped_at", models.DateTimeField(blank=True, null=True)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("next_attempt_at", models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ("last_error", models.CharField(blank=True, max_length=120)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="complaints.complaint")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "read_at", "created_at"], name="notification_inbox_idx"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["sent_at", "next_attempt_at"], name="notification_email_idx"),
        ),
    ]

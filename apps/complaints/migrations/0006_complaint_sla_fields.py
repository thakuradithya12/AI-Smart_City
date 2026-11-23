from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0005_complaint_landmark")]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="priority",
            field=models.CharField(choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")], default="normal", max_length=12),
        ),
        migrations.AddField(
            model_name="complaint",
            name="sla_paused_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="complaint",
            name="sla_breached_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["sla_breached_at", "due_at"], name="complaint_sla_due_idx"),
        ),
    ]

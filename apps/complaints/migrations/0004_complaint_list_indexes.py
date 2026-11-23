from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("complaints", "0003_evidence_thumbnail_path")]

    operations = [
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["status", "due_at"], name="complaint_status_due_idx"),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["department", "status"], name="complaint_dept_status_idx"),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["ward", "status"], name="complaint_ward_status_idx"),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["created_at"], name="complaint_created_idx"),
        ),
    ]

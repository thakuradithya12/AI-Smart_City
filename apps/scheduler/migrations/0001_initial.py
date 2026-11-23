import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SchedulerHeartbeat",
            fields=[
                ("singleton", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("last_seen_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_job", models.CharField(blank=True, max_length=64)),
                ("failed_jobs", models.PositiveIntegerField(default=0)),
            ],
            options={"constraints": [models.CheckConstraint(condition=models.Q(singleton=1), name="scheduler_heartbeat_singleton")]},
        ),
    ]

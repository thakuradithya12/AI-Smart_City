from django.db import models
from django.utils import timezone


class SchedulerHeartbeat(models.Model):
    # One row is shared by all scheduler processes; the lock permits only one writer.
    singleton = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    last_seen_at = models.DateTimeField(default=timezone.now)
    last_job = models.CharField(max_length=64, blank=True)
    failed_jobs = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(singleton=1), name="scheduler_heartbeat_singleton")]

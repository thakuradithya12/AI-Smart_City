from django.conf import settings
from django.db import models

class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    role = models.CharField(max_length=32)
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=120)
    object_id = models.CharField(max_length=120)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Audit events are append-only")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit events are append-only")

from django.db import models

class AiSuggestion(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"
    complaint = models.ForeignKey("complaints.Complaint", on_delete=models.CASCADE, related_name="ai_suggestions")
    label = models.CharField(max_length=64, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    reviewer_decision = models.CharField(max_length=16, blank=True)
    corrected_to = models.ForeignKey("geography.Category", null=True, blank=True, on_delete=models.SET_NULL)

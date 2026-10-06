from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Alert(models.Model):
    class NotifyMethod(models.TextChoices):
        EMAIL = "email", "Email"
        IN_APP = "in_app", "In-app"

    class Frequency(models.TextChoices):
        INSTANT = "instant", "Instant"
        DAILY = "daily", "Daily digest"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    keywords = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    job_type = models.CharField(max_length=100, blank=True)
    notify_method = models.CharField(max_length=10, choices=NotifyMethod.choices, default=NotifyMethod.IN_APP)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.INSTANT)
    digest_time = models.TimeField(default=time(9, 0))
    is_active = models.BooleanField(default=True)
    last_digest_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not (self.keywords or self.location or self.job_type):
            raise ValidationError("At least one of keywords, location, or job_type is required.")

    def __str__(self):
        return f"Alert({self.keywords!r}, {self.location!r}, {self.job_type!r}) for {self.user}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="notifications")
    listing = models.ForeignKey("listings.Listing", on_delete=models.CASCADE, related_name="notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    emailed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification({self.listing} for {self.user})"

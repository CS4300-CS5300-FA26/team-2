from rest_framework import serializers

from tracking.models import Alert, Notification


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id", "keywords", "location", "job_type", "notify_method",
            "frequency", "digest_time", "is_active", "last_digest_sent_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "last_digest_sent_at", "created_at", "updated_at"]

    def validate(self, attrs):
        keywords = attrs.get("keywords", getattr(self.instance, "keywords", ""))
        location = attrs.get("location", getattr(self.instance, "location", ""))
        job_type = attrs.get("job_type", getattr(self.instance, "job_type", ""))
        # kept in sync with models.Alert.clean() — same invariant, enforced separately for the admin-form path.
        if not (keywords or location or job_type):
            raise serializers.ValidationError(
                "At least one of keywords, location, or job_type is required."
            )
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    listing_company = serializers.CharField(source="listing.company", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "alert", "listing", "listing_title", "listing_company", "created_at", "read"]
        read_only_fields = fields

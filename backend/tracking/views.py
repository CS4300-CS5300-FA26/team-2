from rest_framework import viewsets

from tracking.models import Alert, Notification
from tracking.serializers import AlertSerializer, NotificationSerializer


class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

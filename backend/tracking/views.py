from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets

from tracking.models import Alert, Notification
from tracking.serializers import AlertSerializer, NotificationSerializer


# The Alerts page loads this list before any create/edit/delete, so setting the
# csrftoken cookie here guarantees the frontend has a token to send back.
@method_decorator(ensure_csrf_cookie, name="list")
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

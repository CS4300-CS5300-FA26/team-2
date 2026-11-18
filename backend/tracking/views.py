import hmac

from django.conf import settings
from django.core.management import call_command
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes

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


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def run_alerts(request):
    """Run alert matching and emailing. Called on a schedule by .github/workflows/alerts-cron.yml,
    since App Service has no cron. Guarded by a shared bearer token instead of a user session."""
    token = settings.ALERTS_CRON_TOKEN
    # an unresolved Key Vault reference is not a secret; treat it as "not configured"
    if not token or token.startswith("@Microsoft.KeyVault"):
        raise Http404
    supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not hmac.compare_digest(supplied.encode(), token.encode()):
        return JsonResponse({"detail": "Invalid token."}, status=403)
    call_command("run_alert_matching")
    return JsonResponse({"status": "ok"})

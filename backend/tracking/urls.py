from django.urls import path
from rest_framework.routers import DefaultRouter

from tracking.views import AlertViewSet, NotificationViewSet, run_alerts

router = DefaultRouter()
router.register("alerts", AlertViewSet, basename="alert")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = router.urls + [path("internal/run-alerts/", run_alerts)]

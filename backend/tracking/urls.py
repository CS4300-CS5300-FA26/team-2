from rest_framework.routers import DefaultRouter

from tracking.views import AlertViewSet, NotificationViewSet

router = DefaultRouter()
router.register("alerts", AlertViewSet, basename="alert")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = router.urls

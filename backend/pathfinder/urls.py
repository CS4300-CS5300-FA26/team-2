from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

def api_root(request):
    return JsonResponse({"status": "ok", "service": "pathfinder-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root),
    path("api/auth/", include("accounts.urls")),
    path("api/listings/", include("listings.urls")),
    path("api/resumes/", include("resumes.urls")),
    path("api/", include("tracking.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

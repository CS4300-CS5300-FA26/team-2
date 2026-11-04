from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from pathfinder.health import healthz, livez

def api_root(request):
    return JsonResponse({"status": "ok", "service": "pathfinder-api"})


@ensure_csrf_cookie
def api_csrf(request):
    """Frontend bootstrap: cross-site pages can't read the csrftoken cookie
    via document.cookie (it belongs to this API's domain, not theirs), so
    hand the token back in the response body instead. Still sets the cookie
    too -- Django's CsrfViewMiddleware checks the submitted header against it."""
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("livez/", livez),
    path("healthz/", healthz),
    path("api/", api_root),
    path("api/auth/", include("accounts.urls")),
    path("api/listings/", include("listings.urls")),
    path("api/resumes/", include("resumes.urls")),
    path("api/csrf/", api_csrf),
    path("api/", include("tracking.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

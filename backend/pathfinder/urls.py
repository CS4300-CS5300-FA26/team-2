from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from listings import views as listing_views
from accounts import views as account_views
from django.contrib.auth import views as auth_views
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
    path("api/csrf/", api_csrf),
    path("api/", include("tracking.urls")),
    # temporary login page using Django's built in LoginView (works for any user, not just staff)
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="listings/login.html"),
        name="login",
    ),
    path("resumes/", include("resumes.urls")),
    # sign-up page (US1.1)
    path("accounts/signup/", account_views.signup, name="signup"),
    #Run feed view when someone visits the site
    path("feed/", listing_views.feed),
    # clicking an empty bookmark saves it, clicking a filled one removes it
    path("feed/<int:listing_id>/save/", listing_views.save_bookmark),
    path("feed/<int:listing_id>/remove/", listing_views.remove_bookmark),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

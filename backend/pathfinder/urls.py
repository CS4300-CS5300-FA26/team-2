from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from listings import views as listing_views

def api_root(request):
    return JsonResponse({"status": "ok", "service": "pathfinder-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root),
    #Run feed view when someone visits the site
    path("feed/", listing_views.feed),
    #When someone clicks bookmark button, Django is told which code to run
    path("feed/<int:listing_id>/bookmark/", listing_views.toggle_bookmark),
]

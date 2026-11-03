from django.urls import path

from . import api

urlpatterns = [
    path("feed/", api.feed),
    path("saved/", api.saved_jobs),
    path("<int:listing_id>/save/", api.save_bookmark),
    path("<int:listing_id>/remove/", api.remove_bookmark),
    path("<int:listing_id>/notes/", api.add_note),
    path("notes/<int:note_id>/", api.delete_note),
]

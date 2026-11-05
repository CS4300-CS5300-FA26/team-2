from django.urls import path

from . import api

# Mounted at /api/resumes/ ; the React app serves the /resumes/... pages.
app_name = "resumes"

urlpatterns = [
    path("", api.resumes, name="upload"),
    path(
        "<int:resume_id>/feedback/",
        api.resume_feedback,
        name="feedback",
    ),
    path(
        "<int:resume_id>/replace/",
        api.replace_resume,
        name="replace",
    ),
    path(
        "<int:resume_id>/",
        api.delete_resume,
        name="delete",
    ),
]

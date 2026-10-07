# Imports Django's tool for connecting a URL to a view
from django.urls import path

# Imports the views from this resumes app
from . import views


# Namespaces our URLs so Django can tell them apart from other apps
app_name = "resumes"


# Connects the upload URL to the upload_resume view
urlpatterns = [
    path("upload/", views.upload_resume, name="upload"),
]
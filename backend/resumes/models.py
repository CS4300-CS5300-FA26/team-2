# Import Django's configured user model setting
# This lets our Resume model work with the project's current user system
# without hard coding a specific User class
from django.conf import settings

# Import Django's tools for creating database models
from django.db import models


class Resume(models.Model):
    """
    Represents one resume file uploaded by one user.

    This model's only job is to describe the data Django should save
    in the database. It does not handle web pages or file upload requests.
    """

    # Links this resume to the user who uploaded it
    # If the user is deleted, their resume records are deleted too
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
    )

    # Stores the uploaded file.
    # Django will save uploaded files inside MEDIA_ROOT/resumes/
    file = models.FileField(upload_to="resumes/")

    # Automatically stores the date and time when this resume was created
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Gives the resume a readable name in Django's admin area.
        """
        return f"Resume uploaded by {self.owner}"
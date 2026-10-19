# Import Django's built in admin tools
from django.contrib import admin

# Import the Resume model created
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """
    Controls how Resume records appear in Django's admin panel.

    This class only controls the admin display.
    It does not handle file uploads or database logic.
    """

    # These columns will appear in the list of resumes in Django admin
    list_display = ("id", "owner", "file", "uploaded_at")

    # The upload timestamp should be visible but never manually edited
    readonly_fields = ("uploaded_at",)
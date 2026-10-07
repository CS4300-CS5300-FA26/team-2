# Path helps us read the file extension, such as ".pdf"
from pathlib import Path

# Django form tools build and validate HTML forms
from django import forms

# ValidationError lets us show a clear message when a file is not allowed
from django.core.exceptions import ValidationError

# Import the database model this form will create
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    """
    Handles validation for a resume upload.

    This form only validates the file the user chooses.
    The view will assign the resume to the logged in user.
    """

    # Keep the first version simple and safe
    ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}

    # Limits uploads to 5 MB
    MAX_FILE_SIZE = 5 * 1024 * 1024

    class Meta:
        # This form creates a Resume database record
        model = Resume

        # The user chooses only the file
        # Set the owner in the view so users cannot claim another user's resume
        fields = ("file",)

        # The browser will suggest these file types in its file picker
        widgets = {
            "file": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.doc,.docx"}
            )
        }

    def clean_file(self):
        """
        Rejects unsupported or overly large files before saving them.
        """
        uploaded_file = self.cleaned_data["file"]

        # Get the extension from the uploaded filename
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                "Please upload a PDF, DOC, or DOCX resume file."
            )

        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                "Please upload a file smaller than 5 MB."
            )

        # Returning the file means it passed validation
        return uploaded_file
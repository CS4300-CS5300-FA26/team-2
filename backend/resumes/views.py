# Requires a user to be logged in before they can upload a resume
from django.contrib.auth.decorators import login_required

# Gives us tools for rendering pages and redirecting users
from django.shortcuts import redirect, render

# Imports the form that validates uploaded resume files
from .forms import ResumeUploadForm


@login_required
def upload_resume(request):
    """
    Displays the resume upload page and saves valid uploaded files
    """

    # Handles the form when the user submits an upload
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)

        # Saves only after the uploaded file passes our form validation
        if form.is_valid():
            # Creates the Resume object without saving it yet
            resume = form.save(commit=False)

            # Sets the owner on the server so users cannot choose another owner
            resume.owner = request.user

            # Saves the completed Resume object to the database
            resume.save()

            # Redirects after upload so refreshing the page does not upload twice
            return redirect("resumes:upload")

    # Creates an empty form when the user first opens the page
    else:
        form = ResumeUploadForm()

    # Shows only resumes owned by the currently logged in user
    resumes = request.user.resumes.order_by("-uploaded_at")

    # Sends the form and resume list to the HTML template
    return render(
        request,
        "resumes/upload.html",
        {
            "form": form,
            "resumes": resumes,
        },
    )
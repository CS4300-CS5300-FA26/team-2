# Requires a user to be logged in before they can upload a resume
from django.contrib.auth.decorators import login_required


# Shows a message when feedback cannot be created
from django.contrib import messages

# Provides page rendering redirects and secure object lookup
from django.shortcuts import get_object_or_404, redirect, render

# Makes the feedback URL accept button submissions only
from django.views.decorators.http import require_POST

# Validates resume uploads
from .forms import ResumeUploadForm

# Gives the view access to saved resumes
from .models import Resume

# Handles the OpenAI request outside the view
from .services import ResumeFeedbackError, get_resume_feedback


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
@login_required
@require_POST
def request_resume_feedback(request, resume_id):
    """
    Gets AI feedback for one resume owned by the logged in user
    """

    # Only find the resume if it belongs to the logged in user
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        owner=request.user,
    )

    try:
        # Ask the service to review the selected resume
        feedback = get_resume_feedback(resume)

    except ResumeFeedbackError:
        # Return safely instead of exposing a technical API error
        messages.error(
            request,
            "AI feedback is unavailable right now. Please try again later.",
        )
        return redirect("resumes:upload")

    # Send the resume and feedback to the results page
    return render(
        request,
        "resumes/feedback.html",
        {
            "resume": resume,
            "feedback": feedback,
        },
    )
    
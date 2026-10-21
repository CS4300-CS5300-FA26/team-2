# Patch lets the test use fake AI feedback instead of calling OpenAI
from unittest.mock import patch
# These connect Python functions to the Given When and Then sentences
from behave import given, then, when
# This gets the user model used by the project
from django.contrib.auth import get_user_model
# Reverse finds a URL by its Django name
from django.urls import reverse
# Resume lets the test create an uploaded resume
from resumes.models import Resume


@given("I am logged in and have uploaded a resume")
def step_uploaded_resume(context):
    # Create a user only for this test
    context.user = get_user_model().objects.create_user(
        username="resume-feedback-user",
        password="test-password-123",
    )

    # Log in without using the login form
    context.test.client.force_login(context.user)

    # Create a resume record for the logged in user
    context.resume = Resume.objects.create(
        owner=context.user,
        file="resumes/sample-resume.pdf",
    )


@when("I request AI feedback for my resume")
def step_request_feedback(context):
    # Build the URL for this specific resume
    feedback_url = reverse(
        "resumes:feedback",
        args=[context.resume.id],
    )

    # Replace the real service so the test does not call OpenAI
    with patch(
        "resumes.views.get_resume_feedback"
    ) as feedback_function:
        feedback_function.return_value = (
            "- Add measurable results to your experience"
        )

        # This must stay indented inside the with block
        context.response = context.test.client.post(
            feedback_url
        )

@then("I receive suggestions about what could be improved")
def step_receive_feedback(context):
    # A 200 response means the page loaded successfully
    context.test.assertEqual(context.response.status_code, 200)

    # Confirm that the feedback appeared on the page
    context.test.assertContains(
        context.response,
        "Add measurable results to your experience",
    )
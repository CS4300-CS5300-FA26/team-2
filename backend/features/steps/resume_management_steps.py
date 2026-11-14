# These connect Python functions to the When and Then sentences
from behave import then, when

# This creates a small fake uploaded file for the test
from django.core.files.uploadedfile import SimpleUploadedFile

# Reverse finds an API URL by its Django name
from django.urls import reverse

# Resume lets us check whether the record still exists
from resumes.models import Resume


@when("I replace my resume with a new valid file")
def step_replace_resume(context):
    # Remember the original filename so we can confirm it changed
    context.old_file_name = context.resume.file.name

    # Create a valid replacement PDF
    replacement_file = SimpleUploadedFile(
        "updated-resume.pdf",
        b"%PDF-1.4 updated resume",
        content_type="application/pdf",
    )

    # Build the replacement URL for this resume
    replace_url = reverse(
        "resumes:replace",
        args=[context.resume.id],
    )

    # Send the replacement file to the API
    context.response = context.test.client.post(
        replace_url,
        {"file": replacement_file},
    )


@then("the new file replaces my old resume")
def step_confirm_replacement(context):
    # A successful replacement returns 200
    context.test.assertEqual(
        context.response.status_code,
        200,
    )

    # Reload the resume so we see the newest database values
    context.resume.refresh_from_db()

    # Confirm the saved file changed to the replacement
    context.test.assertNotEqual(
        context.resume.file.name,
        context.old_file_name,
    )
    context.test.assertIn(
        "updated-resume",
        context.resume.file.name,
    )

    # Remove the test file and its database record
    context.resume.file.delete(save=False)
    context.resume.delete()


@when("I delete my uploaded resume")
def step_delete_resume(context):
    # Remember the ID because the record will be deleted
    context.resume_id = context.resume.id

    # Build the deletion URL for this resume
    delete_url = reverse(
        "resumes:delete",
        args=[context.resume.id],
    )

    # Send a DELETE request to the API
    context.response = context.test.client.delete(
        delete_url,
    )


@then("the resume is removed from my account")
def step_confirm_deletion(context):
    # A successful deletion returns 204 with no response body
    context.test.assertEqual(
        context.response.status_code,
        204,
    )

    # Confirm the database record no longer exists
    context.test.assertFalse(
        Resume.objects.filter(id=context.resume_id).exists()
    )

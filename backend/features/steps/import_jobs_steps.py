# Given / When / Then connect each line of the .feature file to a function
import json
from io import BytesIO
from unittest.mock import patch  # swaps the real API call for a fake one

from behave import given, when, then
from django.contrib.auth.models import User
from django.core.management import call_command  # runs "python manage.py import_jobs"
from django.test import override_settings

# A fake JobDataLake reply, so this test never spends real credits
FAKE_REPLY = {
    "found": 1,
    "jobs": [
        {
            "title": "Junior Data Analyst",
            "company_name": "Spotify",
            "locations": ["New York, NY"],
            "remote_type": "on_site",
            "url": "https://spotify.com/jobs/456",
            "job_handle": "spotify-junior-data-analyst-xyz789",
        }
    ],
}


# GIVEN: run the import, with a pretend key and the fake reply
@given("the job import has run")
def step_import_has_run(context):
    fake_response = BytesIO(json.dumps(FAKE_REPLY).encode())

    with override_settings(JOBDATALAKE_API_KEY="test-key"):
        with patch("listings.jobdatalake.urlopen", return_value=fake_response):
            call_command("import_jobs")


# WHEN: a logged-in user (who finished sign-up) loads the feed
# Why this user isn't blocked (403):
#   - the feed needs a complete profile: first name, last name, and email (set below)
#   - ProfileStepMiddleware only blocks users who still have an unused email code
#     (an EmailVerification row), and a user made here never gets one
@when("I open the job feed")
def step_open_feed(context):
    user = User.objects.create_user(
        username="importuser",
        password="testpass123",
        first_name="Import",
        last_name="User",
        email="importuser@example.com",
    )
    context.test.client.force_login(user)
    context.response = context.test.client.get("/api/listings/feed/")


# THEN: the imported job is in the feed with its company, location, and apply link
# This checks the feed API (the data the React feed page shows), like the
# project's other Behave scenarios. The React part (JobDetails) has no
# frontend test yet, because the project doesn't have a frontend test tool.
@then("I see the real listings with their company, location, and apply link")
def step_see_real_listing(context):
    context.test.assertEqual(context.response.status_code, 200)

    # find our imported job in the feed by its title
    job = None
    for listing in context.response.json()["listings"]:
        if listing["title"] == "Junior Data Analyst":
            job = listing

    context.test.assertIsNotNone(job)
    context.test.assertEqual(job["company"], "Spotify")
    context.test.assertEqual(job["location"], "New York, NY")
    context.test.assertEqual(job["apply_url"], "https://spotify.com/jobs/456")

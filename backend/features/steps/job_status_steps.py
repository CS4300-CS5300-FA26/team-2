# Sprint 3
# Steps for US4.5 (set a status) and US4.6 (filter by status).
# "Given I am viewing a saved job" is reused from private_note_steps.py,
# so it isn't written again here (Behave shares steps across files).
from behave import given, when, then

from django.contrib.auth.models import User
from listings.models import Bookmark, Listing


# ---------- US4.5 ----------

# WHEN: I pick a status from the dropdown on a saved job
@when('I set its status to "{status}"')
def step_set_status(context, status):
    context.test.client.post(
        f"/api/listings/{context.listing.id}/status/",
        {"status": status},
        content_type="application/json",
    )


# THEN: I come back to Saved Jobs and see the status I picked
@then('the status "{status}" is saved and shown on my Saved Jobs page')
def step_status_shown(context, status):
    response = context.test.client.get("/api/listings/saved/")
    job = response.json()["listings"][0]
    context.test.assertEqual(job["status"], status)


# ---------- US4.6 ----------

# GIVEN: I'm logged in with three saved jobs, each with a different status
@given("I have saved jobs with different statuses")
def step_jobs_with_statuses(context):
    context.user = User.objects.create_user(username="statususer", password="testpass123", first_name="Test", last_name="User", email="statususer@example.com")
    context.test.client.force_login(context.user)

    # (title, status) for each saved job
    jobs = [("Web Intern", "saved"), ("QA Intern", "applied"), ("IT Intern", "interviewing")]
    for title, status in jobs:
        listing = Listing.objects.create(title=title, company="Ball")
        Bookmark.objects.create(user=context.user, listing=listing, status=status)


# WHEN: I choose a status in the "Show" filter at the top of Saved Jobs
@when('I filter my Saved Jobs page by "{status}"')
def step_filter(context, status):
    context.response = context.test.client.get(f"/api/listings/saved/?status={status}")


# THEN: only the matching job is on the page
@then('only the jobs with the status "{status}" are shown')
def step_only_matching(context, status):
    jobs = context.response.json()["listings"]
    context.test.assertEqual([job["title"] for job in jobs], ["QA Intern"])
    for job in jobs:
        context.test.assertEqual(job["status"], status)

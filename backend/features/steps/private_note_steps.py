# Given / When / Then connect each line of the .feature file to a function
from behave import given, when, then

# Django's User model and our own models
from django.contrib.auth.models import User
from listings.models import Bookmark, Listing


# GIVEN: I'm logged in, have one saved job, and I'm on my Saved Jobs page
@given("I am viewing a saved job")
def step_viewing_saved_job(context):
    context.user = User.objects.create_user(username="noteuser", password="testpass123")
    context.test.client.force_login(context.user)

    context.listing = Listing.objects.create(title="Cloud Intern", company="Raytheon")
    Bookmark.objects.create(user=context.user, listing=context.listing)

    # open the Saved Jobs page
    response = context.test.client.get("/saved/")
    context.test.assertContains(response, "Cloud Intern")


# WHEN: I type a note and press "Save note"
@when("I add a private note to it")
def step_add_note(context):
    context.test.client.post(
        f"/saved/{context.listing.id}/note/",
        {"note": "Close to home and great team"},
    )


# THEN: I see my note when I come back, but another user does not
@then("the note is saved and visible only to me when I return to that listing")
def step_note_visible_only_to_me(context):
    # I come back to my Saved Jobs page and see my note
    response = context.test.client.get("/saved/")
    context.test.assertContains(response, "Close to home and great team")

    # another user saves the same job and does NOT see my note
    other_user = User.objects.create_user(username="otheruser", password="testpass123")
    Bookmark.objects.create(user=other_user, listing=context.listing)
    context.test.client.force_login(other_user)

    response = context.test.client.get("/saved/")
    context.test.assertContains(response, "Cloud Intern")
    context.test.assertNotContains(response, "Close to home and great team")

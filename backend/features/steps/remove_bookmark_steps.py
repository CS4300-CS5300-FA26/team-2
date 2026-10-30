# Given / When / Then connect each line of the .feature file to a function
from behave import given, when, then

# Django's User model and our own models
from django.contrib.auth.models import User
from listings.models import Bookmark, Listing


# GIVEN: one job is already saved for a logged-in user
@given("a listing is in my saved jobs list")
def step_listing_is_saved(context):
    context.user = User.objects.create_user(username="removeuser", password="testpass123")
    context.test.client.force_login(context.user)

    context.listing = Listing.objects.create(title="Backend Intern", company="Northrop")
    Bookmark.objects.create(user=context.user, listing=context.listing)


# WHEN: press the Remove button on the Saved Jobs page
@when("I remove the bookmark")
def step_remove_bookmark(context):
    # same form the Remove button sends
    context.test.client.post(
        f"/feed/{context.listing.id}/remove/",
        {"next": "saved"},
    )


# THEN: the job is gone from the Saved Jobs page
@then("the listing no longer appears on my Saved Jobs page")
def step_listing_gone(context):
    response = context.test.client.get("/saved/")

    context.test.assertEqual(response.status_code, 200)
    context.test.assertNotContains(response, "Backend Intern")

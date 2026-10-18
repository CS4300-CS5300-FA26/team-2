# These three words are how Behave knows which function goes with which line
# in the .feature file: "given" = setup, "when" = the action, "then" = the check
from behave import given, when, then

# Django's built-in User model, so we can make a fake user
from django.contrib.auth.models import User

# our own models from the listings app
from listings.models import Bookmark, Listing


# ------------------------------------------------------------
# GIVEN: set up the situation before the test
# This runs for the line: "Given I have bookmarked one or more listings"
# The text inside @given(...) must match the feature file EXACTLY
# ------------------------------------------------------------
@given("I have bookmarked one or more listings")
def step_bookmarked_listings(context):
    # "context" is like a backpack that carries things from one step to the next.
    # Anything we put in it here (like context.user) we can use in later steps.

    # make a fake user for the test
    context.user = User.objects.create_user(username="testuser", password="testpass123")

    # log in as that user (so we don't have to type a password)
    context.test.client.force_login(context.user)

    # make two fake jobs in the test database
    first_job = Listing.objects.create(title="Software Intern", company="MITRE")
    second_job = Listing.objects.create(title="Data Analyst", company="Lockheed")

    # bookmark BOTH jobs for our user
    # (two jobs covers the "one or more" part of the story)
    Bookmark.objects.create(user=context.user, listing=first_job)
    Bookmark.objects.create(user=context.user, listing=second_job)

    # put the saved jobs in the backpack so the "Then" step can check them
    context.saved_jobs = [first_job, second_job]


# ------------------------------------------------------------
# WHEN: do the action we're testing
# This runs for the line: "When I navigate to the Saved Jobs page"
# ------------------------------------------------------------
@when("I navigate to the Saved Jobs page")
def step_navigate_to_saved(context):
    # open the Saved Jobs page, like typing /saved/ in the browser
    # and put the page we get back into the backpack
    context.response = context.test.client.get("/saved/")


# ------------------------------------------------------------
# THEN: check that the right thing happened
# This runs for the line: "Then I see all of my bookmarked listings in one place"
# ------------------------------------------------------------
@then("I see all of my bookmarked listings in one place")
def step_see_all_bookmarks(context):
    # 200 means the page loaded OK
    context.test.assertEqual(context.response.status_code, 200)

    # go through each job we saved, one at a time...
    for job in context.saved_jobs:
        # ...and make sure its title is on the page
        context.test.assertContains(context.response, job.title)

        # ...and its company is on the page too
        context.test.assertContains(context.response, job.company)

    # if all the checks pass, we know ALL our bookmarked jobs
    # show up together on one page, which is what the story asks for

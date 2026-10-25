from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Bookmark, Listing

# get_user_model() gives us whatever User model the project uses,
# so these tests still work if a teammate makes a custom User later
User = get_user_model()


#Any function that starts with test is automatically ran by Django
class FeedPageTests(TestCase):

    # setUp runs before EVERY test, so each test starts fresh.
    # Django also uses a separate, empty test database,
    # so these tests never touch the real data
    def setUp(self):
        # make a regular (not staff) user to test with
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # make a fake job listing to show on the feed
        self.listing = Listing.objects.create(title="Software Intern", company="Lockheed")

        # the addresses the bookmark buttons send to
        self.save_url = "/feed/" + str(self.listing.id) + "/save/"
        self.remove_url = "/feed/" + str(self.listing.id) + "/remove/"

    # TEST 1: the feed page shows listings from the database
    def test_feed_shows_listings_from_database(self):
        self.client.force_login(self.user)

        response = self.client.get("/feed/")

        # 200 means "the page loaded OK"
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Intern")
        self.assertContains(response, "Lockheed")

    # TEST 2: clicking the empty bookmark saves the listing
    def test_save_bookmark(self):
        self.client.force_login(self.user)

        self.client.post(self.save_url)

        self.assertEqual(Bookmark.objects.count(), 1)

    # TEST 3: saving twice (like a double click) still only makes 1 bookmark
    def test_save_twice_only_saves_once(self):
        self.client.force_login(self.user)

        self.client.post(self.save_url)
        self.client.post(self.save_url)

        self.assertEqual(Bookmark.objects.count(), 1)

    # TEST 4: clicking the filled bookmark removes it
    def test_remove_bookmark(self):
        self.client.force_login(self.user)
        Bookmark.objects.create(user=self.user, listing=self.listing)

        self.client.post(self.remove_url)

        self.assertEqual(Bookmark.objects.count(), 0)

    # TEST 5: removing twice doesn't cause an error
    def test_remove_twice_is_fine(self):
        self.client.force_login(self.user)
        Bookmark.objects.create(user=self.user, listing=self.listing)

        self.client.post(self.remove_url)
        response = self.client.post(self.remove_url)

        # 302 means it redirected back to the feed (no crash)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Bookmark.objects.count(), 0)

    # TEST 6: a saved listing shows the filled in icon
    def test_saved_listing_shows_filled_icon(self):
        self.client.force_login(self.user)
        Bookmark.objects.create(user=self.user, listing=self.listing)

        response = self.client.get("/feed/")

        self.assertContains(response, "Remove bookmark")

    # TEST 7: another user's bookmark should NOT show as filled for me
    def test_other_users_bookmarks_are_not_shown(self):
        other_user = User.objects.create_user(username="otheruser", password="testpass123")
        Bookmark.objects.create(user=other_user, listing=self.listing)

        # log in as the first user, who did NOT bookmark it
        self.client.force_login(self.user)
        response = self.client.get("/feed/")

        self.assertNotContains(response, "Remove bookmark")
        self.assertContains(response, "Bookmark listing")

    # TEST 8: bookmarking a listing that doesn't exist gives a 404
    def test_save_missing_listing_gives_404(self):
        self.client.force_login(self.user)

        response = self.client.post("/feed/9999/save/")

        self.assertEqual(response.status_code, 404)

    # TEST 9: visiting the feed while logged out sends you to the login page
    def test_feed_needs_login(self):
        response = self.client.get("/feed/")

        self.assertRedirects(response, "/accounts/login/?next=/feed/")

    # TEST 10: a logged out user can't save a bookmark
    def test_logged_out_cannot_save(self):
        self.client.post(self.save_url)

        self.assertEqual(Bookmark.objects.count(), 0)

    # TEST 11: a regular (not staff) user can log in and see the feed.
    # this would have caught the admin login problem.
    def test_regular_user_can_log_in_and_see_feed(self):
        response = self.client.post(
            "/accounts/login/",
            {"username": "testuser", "password": "testpass123", "next": "/feed/"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Intern")
    # Test 12: 
    # the feed should have a link to the Saved Jobs page
    def test_feed_has_link_to_saved_jobs(self):
        self.client.force_login(self.user)
        response = self.client.get("/feed/")

        # check the link is on the page
        self.assertContains(response, 'href="/saved/"')
    
    # Test 13: To get model.py to 100% in Coverage
    # a listing should show as "Title at Company" (used on the admin page)
    def test_listing_str(self):
        self.assertEqual(str(self.listing), "Software Intern at Lockheed")

#Sprint 1
# Tests for the Saved Jobs page
# The page lives at /saved/ and should show only MY bookmarked jobs
class SavedJobsPageTests(TestCase):

    # setUp runs before every test, so each test starts with the same fake data
    def setUp(self):
        # make two fake users: me and another person
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123")

        # make two fake jobs
        self.saved_job = Listing.objects.create(title="Software Intern", company="Acme")
        self.unsaved_job = Listing.objects.create(title="Data Analyst", company="Globex")

        # I bookmark ONLY the first job
        Bookmark.objects.create(user=self.user, listing=self.saved_job)


    # TEST 1: I should see the job I saved
    def test_shows_my_saved_jobs(self):
        # log in as me
        self.client.force_login(self.user)

        # open the saved jobs page
        response = self.client.get("/saved/")

        # 200 = the page loaded OK
        self.assertEqual(response.status_code, 200)

        # the job I saved should be on the page
        self.assertContains(response, "Software Intern")


    # TEST 2: I should NOT see a job I didn't save
    def test_does_not_show_unsaved_jobs(self):
        self.client.force_login(self.user)
        response = self.client.get("/saved/")

        # assertNotContains = make sure this text is NOT on the page
        self.assertNotContains(response, "Data Analyst")


    # TEST 3: I should NOT see jobs that other people saved
    def test_does_not_show_other_users_bookmarks(self):
        # the other user saves the Data Analyst job (I never saved it)
        Bookmark.objects.create(user=self.other_user, listing=self.unsaved_job)

        # log in as me, not them
        self.client.force_login(self.user)
        response = self.client.get("/saved/")

        # their bookmark should not show up on MY page
        self.assertNotContains(response, "Data Analyst")


    # TEST 4: if I saved nothing, show a message instead of a blank page
    def test_shows_message_when_nothing_saved(self):
        # the other user has no bookmarks yet, so log in as them
        self.client.force_login(self.other_user)
        response = self.client.get("/saved/")

        # this exact message should be on the page
        self.assertContains(response, "You haven't saved any jobs yet.")


    # TEST 5: you have to be logged in to see saved jobs
    def test_saved_page_needs_login(self):
        # no login here on purpose
        response = self.client.get("/saved/")

        # 302 = Django sent us to the login page instead
        self.assertEqual(response.status_code, 302)



#Sprint 2
# Tests for US4.3: removing a bookmark from the Saved Jobs page
class RemoveFromSavedPageTests(TestCase):

    # setUp runs before every test: one user with one saved job
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.listing = Listing.objects.create(title="Software Intern", company="MITRE")
        Bookmark.objects.create(user=self.user, listing=self.listing)

        # the address the Remove button sends the form to
        self.remove_url = f"/feed/{self.listing.id}/remove/"

        # log in for every test in this class
        self.client.force_login(self.user)


    # TEST 1: each saved job has a Remove button
    def test_saved_page_has_remove_button(self):
        response = self.client.get("/saved/")

        # the button's form should send to this job's remove address
        self.assertContains(response, f'action="{self.remove_url}"')


    # TEST 2: removing from the Saved Jobs page sends you back to Saved Jobs
    def test_remove_from_saved_page_goes_back_to_saved(self):
        # "next": "saved" is the hidden field the Remove button sends
        response = self.client.post(self.remove_url, {"next": "saved"})

        self.assertRedirects(response, "/saved/")


    # TEST 3: after removing, the job is no longer on the Saved Jobs page
    def test_removed_job_not_on_saved_page(self):
        self.client.post(self.remove_url, {"next": "saved"})
        response = self.client.get("/saved/")

        self.assertNotContains(response, "Software Intern")
        self.assertContains(response, "You haven't saved any jobs yet.")


    # TEST 4: removing from the feed still sends you back to the feed
    # (makes sure we didn't break US4.1)
    def test_remove_from_feed_still_goes_to_feed(self):
        response = self.client.post(self.remove_url)

        self.assertRedirects(response, "/feed/")
   
    # TEST 5: removing my bookmark doesn't remove someone else's bookmark
    # for the same job
    def test_remove_does_not_affect_other_users(self):
        # another user saves the same job
        other_user = User.objects.create_user(username="otheruser", password="testpass123")
        Bookmark.objects.create(user=other_user, listing=self.listing)

        # I remove my bookmark
        self.client.post(self.remove_url, {"next": "saved"})

        # mine is gone, theirs is still there
        self.assertFalse(Bookmark.objects.filter(user=self.user, listing=self.listing).exists())
        self.assertTrue(Bookmark.objects.filter(user=other_user, listing=self.listing).exists())

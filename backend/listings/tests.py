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

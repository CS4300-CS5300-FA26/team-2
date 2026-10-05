from django.contrib.auth.models import User
from django.test import TestCase

from .models import Bookmark, Listing


#Any function that starts with test is automicatically ran by Django
class FeedPageTests(TestCase):

    # setUp runs before EVERY test, so each test starts fresh.
    # Django also uses a separate, empty test database,
    # so these tests never touch the data
    def setUp(self):
        # make a fake user to log in with
        self.user = User.objects.create_user(username="testuser", password="password")

        # make a fake job listing to show on the feed
        self.listing = Listing.objects.create(title="Software Intern", company="Lockheed")


    # TEST 1: the feed page should show listings from the database
    def test_feed_page_shows_listings_from_database(self):
        # log in as our fake user (skips typing a password)
        self.client.force_login(self.user)

        # visit the feed page, like opening it in a browser
        response = self.client.get("/feed/")

        # 200 means "the page loaded OK"
        self.assertEqual(response.status_code, 200)

        # check that the job title and company show up on the page
        self.assertContains(response, "Software Intern")
        self.assertContains(response, "Lockheed")


    # TEST 2: clicking the bookmark button should save the listing
    def test_clicking_bookmark_saves_listing(self):
        self.client.force_login(self.user)

        # "click" the bookmark button once
        # (post means we're sending the form, like clicking the button)
        self.client.post(f"/feed/{self.listing.id}/bookmark/")

        # look in the database: is there a bookmark for this user and listing?
        saved = Bookmark.objects.filter(user=self.user, listing=self.listing).exists()

        # there should be one now
        self.assertTrue(saved)


    # TEST 3: clicking the bookmark a second time should remove it
    def test_clicking_bookmark_again_removes_it(self):
        self.client.force_login(self.user)

        # click once to save it...
        self.client.post(f"/feed/{self.listing.id}/bookmark/")
        # ...then click again to unsave it
        self.client.post(f"/feed/{self.listing.id}/bookmark/")

        # look in the database again
        saved = Bookmark.objects.filter(user=self.user, listing=self.listing).exists()

        # the bookmark should be gone
        self.assertFalse(saved)


    # TEST 4: a saved listing should show the filled-in bookmark icon
    def test_saved_listing_shows_filled_icon(self):
        self.client.force_login(self.user)

        # save the listing directly in the database (no clicking needed)
        Bookmark.objects.create(user=self.user, listing=self.listing)

        # load the feed page
        response = self.client.get("/feed/")

        # "Remove bookmark" only appears on the filled-in button,
        # so if we see it, the icon is filled in
        self.assertContains(response, "Remove bookmark")


    # TEST 5: you should have to log in to see the feed
    def test_feed_page_needs_login(self):
        # notice: NO force_login here, so we're a logged-out visitor
        response = self.client.get("/feed/")

        # 302 means "redirect", so Django sent us to the login page
        # instead of showing the feed
        self.assertEqual(response.status_code, 302)

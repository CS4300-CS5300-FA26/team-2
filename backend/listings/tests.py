from django.contrib.auth import get_user_model
from django.test import TestCase

from ai_intelligence.models import CredibilityScore

from .models import Bookmark, Listing, Note

User = get_user_model()

FEED = "/api/listings/feed/"
SAVED = "/api/listings/saved/"


class ApiTestCase(TestCase):
    """Shared helpers: users, one listing, JSON posting."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123")
        self.listing = Listing.objects.create(title="Software Intern", company="Lockheed")
        self.save_url = f"/api/listings/{self.listing.id}/save/"
        self.remove_url = f"/api/listings/{self.listing.id}/remove/"
        self.add_url = f"/api/listings/{self.listing.id}/notes/"

    def titles(self, url):
        return [l["title"] for l in self.client.get(url).json()["listings"]]

    def add_note(self, text, url=None):
        return self.client.post(url or self.add_url, {"note": text}, content_type="application/json")


class FeedApiTests(ApiTestCase):
    def test_feed_shows_listings_from_database(self):
        self.client.force_login(self.user)
        response = self.client.get(FEED)
        self.assertEqual(response.status_code, 200)
        item = response.json()["listings"][0]
        self.assertEqual((item["title"], item["company"]), ("Software Intern", "Lockheed"))

    def test_save_bookmark(self):
        self.client.force_login(self.user)
        response = self.client.post(self.save_url)
        self.assertEqual(response.json(), {"id": self.listing.id, "saved": True})
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_save_twice_only_saves_once(self):
        self.client.force_login(self.user)
        self.client.post(self.save_url)
        self.client.post(self.save_url)
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_remove_bookmark(self):
        self.client.force_login(self.user)
        Bookmark.objects.create(user=self.user, listing=self.listing)
        self.client.post(self.remove_url)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_remove_twice_is_fine(self):
        self.client.force_login(self.user)
        Bookmark.objects.create(user=self.user, listing=self.listing)
        self.client.post(self.remove_url)
        response = self.client.post(self.remove_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_saved_listing_is_flagged_saved(self):
        self.client.force_login(self.user)
        Bookmark.objects.create(user=self.user, listing=self.listing)
        self.assertTrue(self.client.get(FEED).json()["listings"][0]["saved"])

    def test_other_users_bookmarks_are_not_shown(self):
        Bookmark.objects.create(user=self.other_user, listing=self.listing)
        self.client.force_login(self.user)
        self.assertFalse(self.client.get(FEED).json()["listings"][0]["saved"])

    def test_save_missing_listing_gives_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post("/api/listings/9999/save/").status_code, 404)

    def test_remove_missing_listing_gives_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post("/api/listings/9999/remove/").status_code, 404)

    def test_feed_needs_login(self):
        response = self.client.get(FEED)
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.json())

    def test_logged_out_cannot_save_or_remove(self):
        self.assertEqual(self.client.post(self.save_url).status_code, 401)
        self.assertEqual(self.client.post(self.remove_url).status_code, 401)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_save_get_not_allowed(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.save_url).status_code, 405)

    def test_regular_user_can_log_in_and_see_feed(self):
        self.client.post(
            "/api/auth/login",
            {"username": "testuser", "password": "testpass123"},
            content_type="application/json",
        )
        self.assertEqual(self.titles(FEED), ["Software Intern"])

    def test_unscored_listing_has_null_score(self):
        self.client.force_login(self.user)
        item = self.client.get(FEED).json()["listings"][0]
        self.assertIsNone(item["score"])
        self.assertEqual(item["reasoning"], "")

    def test_scored_listing_includes_score_and_reasoning(self):
        CredibilityScore.objects.update_or_create(
            listing=self.listing, defaults={"score": 82, "reasoning": "Verified employer"}
        )
        self.client.force_login(self.user)
        item = self.client.get(FEED).json()["listings"][0]
        self.assertEqual((item["score"], item["reasoning"]), (82, "Verified employer"))

    def test_listing_str(self):
        self.assertEqual(str(self.listing), "Software Intern at Lockheed")


class SavedJobsApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.unsaved_job = Listing.objects.create(title="Data Analyst", company="Globex")
        Bookmark.objects.create(user=self.user, listing=self.listing)
        self.client.force_login(self.user)

    def test_shows_my_saved_jobs(self):
        response = self.client.get(SAVED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.titles(SAVED), ["Software Intern"])

    def test_does_not_show_other_users_bookmarks(self):
        Bookmark.objects.create(user=self.other_user, listing=self.unsaved_job)
        self.assertNotIn("Data Analyst", self.titles(SAVED))

    def test_empty_list_when_nothing_saved(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(SAVED).json(), {"listings": []})

    def test_saved_needs_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(SAVED).status_code, 401)


class RemoveFromSavedTests(ApiTestCase):
    """US4.3 server side. The confirm dialog lives in the React page."""

    def setUp(self):
        super().setUp()
        Bookmark.objects.create(user=self.user, listing=self.listing)
        self.client.force_login(self.user)

    def test_removed_job_not_on_saved_list(self):
        self.client.post(self.remove_url)
        self.assertEqual(self.client.get(SAVED).json(), {"listings": []})

    def test_remove_does_not_affect_other_users(self):
        Bookmark.objects.create(user=self.other_user, listing=self.listing)
        self.client.post(self.remove_url)
        self.assertFalse(Bookmark.objects.filter(user=self.user, listing=self.listing).exists())
        self.assertTrue(Bookmark.objects.filter(user=self.other_user, listing=self.listing).exists())

    def test_remove_also_deletes_notes(self):
        Note.objects.create(bookmark=Bookmark.objects.get(user=self.user), text="bye")
        self.client.post(self.remove_url)
        self.assertEqual(Note.objects.count(), 0)


class PrivateNoteTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.bookmark = Bookmark.objects.create(user=self.user, listing=self.listing)

    def delete_url(self, note):
        return f"/api/listings/notes/{note.id}/"

    def test_add_note_saves_it(self):
        self.client.force_login(self.user)
        response = self.add_note("Great mentorship program")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["text"], "Great mentorship program")
        self.assertEqual(Note.objects.filter(bookmark=self.bookmark).count(), 1)
        notes = self.client.get(SAVED).json()["listings"][0]["notes"]
        self.assertEqual([n["text"] for n in notes], ["Great mentorship program"])

    def test_add_second_note_keeps_first(self):
        self.client.force_login(self.user)
        self.add_note("First reason")
        self.add_note("Second reason")
        notes = self.client.get(SAVED).json()["listings"][0]["notes"]
        self.assertEqual([n["text"] for n in notes], ["First reason", "Second reason"])

    def test_empty_note_not_saved(self):
        self.client.force_login(self.user)
        self.assertEqual(self.add_note("   ").status_code, 400)
        self.assertEqual(Note.objects.count(), 0)

    def test_malformed_body_not_saved(self):
        self.client.force_login(self.user)
        response = self.client.post(self.add_url, "not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Note.objects.count(), 0)

    def test_notes_only_visible_to_me(self):
        Bookmark.objects.create(user=self.other_user, listing=self.listing)
        self.client.force_login(self.user)
        self.add_note("My secret reason")
        self.client.force_login(self.other_user)
        item = self.client.get(SAVED).json()["listings"][0]
        self.assertEqual(item["title"], "Software Intern")
        self.assertEqual(item["notes"], [])

    def test_cannot_add_note_without_bookmark(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.add_note("Sneaky note").status_code, 404)
        self.assertEqual(Note.objects.count(), 0)

    def test_add_note_needs_login(self):
        self.assertEqual(self.add_note("Hello").status_code, 401)
        self.assertEqual(Note.objects.count(), 0)

    def test_add_note_get_not_allowed(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.add_url).status_code, 405)

    def test_delete_removes_only_that_note(self):
        keep = Note.objects.create(bookmark=self.bookmark, text="Keep this one")
        remove = Note.objects.create(bookmark=self.bookmark, text="Remove this one")
        self.client.force_login(self.user)
        self.assertEqual(self.client.delete(self.delete_url(remove)).status_code, 200)
        self.assertTrue(Note.objects.filter(id=keep.id).exists())
        self.assertFalse(Note.objects.filter(id=remove.id).exists())

    def test_cannot_delete_other_users_note(self):
        note = Note.objects.create(bookmark=self.bookmark, text="My note")
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.delete(self.delete_url(note)).status_code, 404)
        self.assertTrue(Note.objects.filter(id=note.id).exists())

    def test_delete_needs_login(self):
        note = Note.objects.create(bookmark=self.bookmark, text="My note")
        self.assertEqual(self.client.delete(self.delete_url(note)).status_code, 401)
        self.assertTrue(Note.objects.filter(id=note.id).exists())

    def test_delete_get_not_allowed(self):
        note = Note.objects.create(bookmark=self.bookmark, text="Still here")
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.delete_url(note)).status_code, 405)
        self.assertTrue(Note.objects.filter(id=note.id).exists())

    def test_note_str(self):
        note = Note.objects.create(bookmark=self.bookmark, text="Remember the 401k match")
        self.assertEqual(str(note), "Remember the 401k match")

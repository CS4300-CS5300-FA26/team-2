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
        self.user = User.objects.create_user(username="testuser", password="testpass123", first_name="Test", last_name="User", email="testuser@example.com")
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123", first_name="Test", last_name="User", email="otheruser@example.com")
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


class ProfileGateTests(TestCase):
    def test_incomplete_profile_cannot_use_listings_api(self):
        user = User.objects.create_user(username="nofill", password="testpass123")
        self.client.force_login(user)
        for url in (FEED, "/api/listings/saved/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["detail"], "Complete your profile first.")

#Sprint 3
# Tests for importing real jobs from the JobDataLake API.
#
# IMPORTANT: these tests never call the real API.
# "patch" swaps the real urlopen (the thing that calls the website) for a fake,
# and we tell the fake what to reply. So the tests are fast, work offline,
# and never spend our credits.

# (these imports are down here so this whole block can be pasted at the end of the file)
import json  # to build a fake JSON reply
from io import BytesIO  # makes text act like a reply from a website
from unittest.mock import patch  # swaps real code for a fake during a test
from urllib.error import HTTPError, URLError  # the errors urlopen can raise

from django.core.management import call_command  # runs "python manage.py ..." inside a test
from django.core.management.base import CommandError
from django.test import override_settings  # pretend a setting has a different value


# One fake job, shaped exactly like a job in the API's real reply
FAKE_JOB = {
    "title": "Software Engineer Intern",
    "company_name": "Stripe",
    "locations": ["San Francisco, CA", "Remote"],
    "remote_type": "hybrid",
    "url": "https://stripe.com/jobs/123",
    "job_handle": "stripe-software-engineer-intern-abc123",
}


# Helper: build a fake API reply that contains these jobs
def fake_reply(jobs):
    reply = {"found": len(jobs), "jobs": jobs}
    return BytesIO(json.dumps(reply).encode())


# override_settings gives every test in this class a pretend API key
@override_settings(JOBDATALAKE_API_KEY="test-key")
class ImportJobsTests(ApiTestCase):

    # TEST 1: importing saves the job with all its details
    # @patch(...) replaces urlopen, and the fake is passed in as "mock_urlopen"
    @patch("listings.jobdatalake.urlopen")
    def test_import_saves_new_jobs(self, mock_urlopen):
        # when our code calls the API, the fake replies with our one job
        mock_urlopen.return_value = fake_reply([FAKE_JOB])

        call_command("import_jobs", "--query", "software intern")

        job = Listing.objects.get(external_id="stripe-software-engineer-intern-abc123")
        self.assertEqual(job.title, "Software Engineer Intern")
        self.assertEqual(job.company, "Stripe")
        self.assertEqual(job.location, "San Francisco, CA; Remote")
        self.assertEqual(job.remote_type, "hybrid")
        self.assertEqual(job.apply_url, "https://stripe.com/jobs/123")

    # TEST 2: importing the same job twice doesn't make a copy
    @patch("listings.jobdatalake.urlopen")
    def test_import_skips_jobs_already_saved(self, mock_urlopen):
        # side_effect = a list of replies, one for each call
        mock_urlopen.side_effect = [fake_reply([FAKE_JOB]), fake_reply([FAKE_JOB])]

        call_command("import_jobs")  # first time: saves the job
        call_command("import_jobs")  # second time: same job, should be skipped

        self.assertEqual(Listing.objects.filter(external_id=FAKE_JOB["job_handle"]).count(), 1)

    # TEST 3: the request sends our key and the search options
    @patch("listings.jobdatalake.urlopen")
    def test_import_sends_key_and_options(self, mock_urlopen):
        mock_urlopen.return_value = fake_reply([])

        call_command("import_jobs", "--query", "data analyst", "--limit", "5")

        # look at the request our code tried to send
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.get_header("X-api-key"), "test-key")
        # we name ourselves, because JobDataLake blocks the default "Python-urllib" name
        self.assertEqual(request.get_header("User-agent"), "Pathfinder/1.0 (CS4300 student project)")
        self.assertIn("q=data+analyst", request.full_url)
        self.assertIn("per_page=5", request.full_url)
        self.assertIn("countries=US", request.full_url)

    # TEST 4: an apply link that isn't a normal web address is not saved
    @patch("listings.jobdatalake.urlopen")
    def test_unsafe_apply_link_is_dropped(self, mock_urlopen):
        # copy the fake job, then change the link to a dangerous one
        bad_job = FAKE_JOB.copy()
        bad_job["url"] = "javascript:alert(1)"
        bad_job["job_handle"] = "bad-link-job"
        mock_urlopen.return_value = fake_reply([bad_job])

        call_command("import_jobs")

        self.assertEqual(Listing.objects.get(external_id="bad-link-job").apply_url, "")

    # TEST 5: out of credits (error 402) gives a clear error and saves nothing
    @patch("listings.jobdatalake.urlopen")
    def test_out_of_credits_gives_clear_error(self, mock_urlopen):
        # side_effect = an error makes the fake RAISE that error instead of replying
        mock_urlopen.side_effect = HTTPError("url", 402, "Payment Required", {}, None)
        count_before = Listing.objects.count()

        # the command should stop with a message that contains "out of credits"
        with self.assertRaisesMessage(CommandError, "out of credits"):
            call_command("import_jobs")

        self.assertEqual(Listing.objects.count(), count_before)

    # TEST 6: no API key gives a clear error and never calls the API
    @override_settings(JOBDATALAKE_API_KEY="")  # pretend the key is missing
    @patch("listings.jobdatalake.urlopen")
    def test_missing_key_gives_clear_error(self, mock_urlopen):
        with self.assertRaisesMessage(CommandError, "JOBDATALAKE_API_KEY"):
            call_command("import_jobs")

        mock_urlopen.assert_not_called()  # no request was sent, so no credit was spent

    # TEST 7: the feed sends the location and apply link to the React page
    def test_feed_includes_location_and_apply_link(self):
        # give the test listing a location and link
        self.listing.location = "Denver, CO"
        self.listing.apply_url = "https://example.com/apply"
        self.listing.save()
        self.client.force_login(self.user)

        item = self.client.get(FEED).json()["listings"][0]

        self.assertEqual(item["location"], "Denver, CO")
        self.assertEqual(item["apply_url"], "https://example.com/apply")

    # TEST 8: if JobDataLake can't be reached, it gives a clear error
    @patch("listings.jobdatalake.urlopen")
    def test_network_error_gives_clear_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("connection refused")

        with self.assertRaisesMessage(CommandError, "Could not reach JobDataLake"):
            call_command("import_jobs")

    # TEST 9: each kind of API error gives its own clear message
    @patch("listings.jobdatalake.urlopen")
    def test_other_api_errors_give_clear_messages(self, mock_urlopen):
        # error code from the API -> words we expect in the message
        expected_messages = {
            401: "API key is invalid",
            429: "Too many requests",
            500: "JobDataLake error 500",
        }
        for code, message in expected_messages.items():
            # subTest shows which code failed, if one does
            with self.subTest(code=code):
                mock_urlopen.side_effect = HTTPError("url", code, "Error", {}, None)

                with self.assertRaisesMessage(CommandError, message):
                    call_command("import_jobs")

    # TEST 10: the limit is kept between 1 and 100 (what the API allows)
    @patch("listings.jobdatalake.urlopen")
    def test_limit_is_kept_between_1_and_100(self, mock_urlopen):
        # a fresh fake reply for each of the two calls
        mock_urlopen.side_effect = [fake_reply([]), fake_reply([])]

        call_command("import_jobs", "--limit", "500")  # too big
        call_command("import_jobs", "--limit", "0")    # too small

        # look at the two requests our code sent
        first_request = mock_urlopen.call_args_list[0][0][0]
        second_request = mock_urlopen.call_args_list[1][0][0]
        self.assertIn("per_page=100", first_request.full_url)
        self.assertIn("per_page=1&", second_request.full_url)


#Sprint 3: tests for importing tech jobs
@override_settings(JOBDATALAKE_API_KEY="test-key")
class ImportJobsFunctionTests(ApiTestCase):

    # TEST 11: by default we ask for any tech (eng) job
    @patch("listings.jobdatalake.urlopen")
    def test_import_asks_for_tech_jobs_by_default(self, mock_urlopen):
        mock_urlopen.return_value = fake_reply([])

        call_command("import_jobs")

        # look at the request our code tried to send
        request = mock_urlopen.call_args[0][0]
        self.assertIn("q=%2A", request.full_url)  # "*" = any job title
        self.assertIn("job_function=eng", request.full_url)

    # TEST 12: --function picks another kind of job (uppercase works too)
    @patch("listings.jobdatalake.urlopen")
    def test_import_can_ask_for_another_function(self, mock_urlopen):
        mock_urlopen.return_value = fake_reply([])

        call_command("import_jobs", "--function", "DATA")

        request = mock_urlopen.call_args[0][0]
        self.assertIn("job_function=data", request.full_url)

    # TEST 13: --function "" means any kind of job, so we don't send it at all
    @patch("listings.jobdatalake.urlopen")
    def test_import_with_empty_function_sends_no_filter(self, mock_urlopen):
        mock_urlopen.return_value = fake_reply([])

        call_command("import_jobs", "--function", "")

        request = mock_urlopen.call_args[0][0]
        self.assertNotIn("job_function=", request.full_url)
#Sprint 3
# US4.5: set a status on a saved job (saved, applied, interviewing, offer, rejected)
# US4.6: filter my Saved Jobs page by status
# Also: each note shows the date and time it was written
class JobStatusTests(ApiTestCase):

    def setUp(self):
        super().setUp()  # runs ApiTestCase's setUp first (users and one listing)
        self.client.force_login(self.user)
        # this user saves the listing, so it's on their Saved Jobs page
        self.bookmark = Bookmark.objects.create(user=self.user, listing=self.listing)
        self.status_url = f"/api/listings/{self.listing.id}/status/"

    # helper: send a new status for the saved job
    def set_status(self, status):
        return self.client.post(self.status_url, {"status": status}, content_type="application/json")

    # TEST 1: a newly saved job starts as "saved"
    def test_new_saved_job_has_status_saved(self):
        job = self.client.get(SAVED).json()["listings"][0]
        self.assertEqual(job["status"], "saved")

    # TEST 2: setting a status saves it and shows it on the Saved Jobs page
    def test_set_status_saves_and_shows_it(self):
        response = self.set_status("applied")
        self.assertEqual(response.status_code, 200)

        self.bookmark.refresh_from_db()  # reload it from the database
        self.assertEqual(self.bookmark.status, "applied")
        job = self.client.get(SAVED).json()["listings"][0]
        self.assertEqual(job["status"], "applied")

    # TEST 3: every one of the five statuses works
    def test_all_five_statuses_work(self):
        for status in ["saved", "applied", "interviewing", "offer", "rejected"]:
            self.assertEqual(self.set_status(status).status_code, 200)

    # TEST 4: a made-up status is refused and nothing changes
    def test_unknown_status_is_refused(self):
        response = self.set_status("hired!!")
        self.assertEqual(response.status_code, 400)
        self.bookmark.refresh_from_db()
        self.assertEqual(self.bookmark.status, "saved")

    # TEST 5: you can't set a status on a job you haven't saved
    def test_cannot_set_status_on_job_not_saved(self):
        self.client.force_login(self.other_user)  # other_user never saved it
        self.assertEqual(self.set_status("applied").status_code, 404)

    # TEST 6: logged-out users can't set a status
    def test_set_status_needs_login(self):
        self.client.logout()
        self.assertEqual(self.set_status("applied").status_code, 401)

    # TEST 7: only POST is allowed for setting a status
    def test_set_status_get_not_allowed(self):
        self.assertEqual(self.client.get(self.status_url).status_code, 405)

    # TEST 8 (US4.6): filtering shows only jobs with that status
    def test_filter_shows_only_matching_jobs(self):
        # a second saved job that we mark as "applied"
        other_job = Listing.objects.create(title="Data Intern", company="Ball")
        Bookmark.objects.create(user=self.user, listing=other_job, status="applied")

        self.assertEqual(self.titles(SAVED + "?status=applied"), ["Data Intern"])
        self.assertEqual(self.titles(SAVED + "?status=saved"), ["Software Intern"])

    # TEST 9 (US4.6): no filter means every saved job is shown
    def test_no_filter_shows_all_jobs(self):
        other_job = Listing.objects.create(title="Data Intern", company="Ball")
        Bookmark.objects.create(user=self.user, listing=other_job, status="applied")
        self.assertEqual(len(self.titles(SAVED)), 2)

    # TEST 10 (US4.6): a made-up filter is refused
    def test_unknown_filter_is_refused(self):
        self.assertEqual(self.client.get(SAVED + "?status=nope").status_code, 400)

    # TEST 11: notes include the date and time they were written
    def test_notes_include_date_and_time(self):
        response = self.add_note("Call the recruiter")
        self.assertIn("created_at", response.json())

        note = self.client.get(SAVED).json()["listings"][0]["notes"][0]
        self.assertEqual(note["text"], "Call the recruiter")
        self.assertIn("created_at", note)

    # TEST 12: a broken request (not real JSON) is refused and nothing changes
    def test_broken_request_is_refused(self):
        response = self.client.post(self.status_url, "not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.bookmark.refresh_from_db()
        self.assertEqual(self.bookmark.status, "saved")

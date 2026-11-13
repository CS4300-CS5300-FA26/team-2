from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase    # Obviously needed
from django.utils import timezone

# Local Models and functions
from .models import CredibilityScore
from listings.models import Listing
from .signals import parse_credibility_response

# Error types
from django.db import IntegrityError
from openai import OpenAIError

# https://docs.python.org/3/library/unittest.mock.html
from unittest.mock import patch
import os

class FilterSortingTests(TestCase):

    def setUp(self):
        openai_patcher = patch("ai_intelligence.signals.OpenAI")
        self.mock_openai = openai_patcher.start()
        self.addCleanup(openai_patcher.stop)
        self.mock_openai.return_value.chat.completions.create.return_value.choices[0].message.content = (
            "Reasons: Test score; Final Score: 82"
        )

        user = get_user_model().objects.create_user(
            username="filter-test-user", password="test-pass",
            first_name="Filter", last_name="Tester", email="filter@example.com",
        )
        self.client.force_login(user)

        base_time = timezone.now()
        self.listings = []
        for index, score in enumerate((40, 60, 80, 90)):
            listing = Listing.objects.create(
                title=f"Score {score}",
                company="Test company",
            )
            CredibilityScore.objects.filter(listing=listing).update(score=score)
            Listing.objects.filter(pk=listing.pk).update(
                created_at=base_time + timedelta(days=index)
            )
            self.listings.append(listing)

        self.unscored_listing = Listing.objects.create(
            title="Unscored listing",
            company="Test company",
        )
        CredibilityScore.objects.filter(listing=self.unscored_listing).update(score=None)

    def apply_filters(self, sort_by, min_score="40", max_score="80"):
        # US3.3 now lives on the JSON feed: GET /api/listings/feed/?sort_by=&min_score=&max_score=
        return self.client.get("/api/listings/feed/", {
            "sort_by": sort_by,
            "min_score": min_score,
            "max_score": max_score,
        })

    def titles(self, response):
        return [l["title"] for l in response.json()["listings"]]

    def test_score_range_includes_endpoints_and_excludes_out_of_range(self):
        response = self.apply_filters("date-asc")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.titles(response), ["Score 40", "Score 60", "Score 80"])

    def test_sort_choices_order_filtered_listings(self):
        expected_titles = {
            "date-desc": ["Score 80", "Score 60", "Score 40"],
            "date-asc": ["Score 40", "Score 60", "Score 80"],
            "score-desc": ["Score 80", "Score 60", "Score 40"],
            "score-asc": ["Score 40", "Score 60", "Score 80"],
        }

        for sort_by, titles in expected_titles.items():
            with self.subTest(sort_by=sort_by):
                response = self.apply_filters(sort_by)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.titles(response), titles)

    def test_feed_without_query_string_is_unchanged(self):
        # no query string -> nothing is filtered out, so the unscored listing is still shown
        response = self.client.get("/api/listings/feed/")

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            self.titles(response),
            ["Score 40", "Score 60", "Score 80", "Score 90", "Unscored listing"],
        )

    def test_invalid_filter_input_is_rejected(self):
        bad_requests = [
            {"sort_by": "bogus"},
            {"sort_by": "date-asc", "min_score": "abc", "max_score": "80"},
            {"sort_by": "date-asc", "min_score": "70", "max_score": "30"},   # min > max
            {"sort_by": "date-asc", "min_score": "-5", "max_score": "80"},
            {"sort_by": "date-asc", "min_score": "0", "max_score": "101"},
        ]
        for params in bad_requests:
            with self.subTest(params=params):
                self.assertEqual(self.client.get("/api/listings/feed/", params).status_code, 400)


class AiTests(TestCase):
    
    def setUp(self):
        
        # Create mock AI for tests
        self.openai_patcher = patch("ai_intelligence.signals.OpenAI")
        self.mock_openai = self.openai_patcher.start()
        self.addCleanup(self.openai_patcher.stop)
        self.mock_openai.return_value.chat.completions.create.return_value.choices[0].message.content = (
            "Reasons: Consistent company, clear title; Final Score: 82"
        )

        # Create listing for the credibility score to be attached to
        self.listing = Listing.objects.create(title="job", company="company")

    # Test | If the AI call fails, the listing is still saved with an N/A credibility score
    def test_listing_is_saved_when_ai_call_fails(self):
        
        # Return failed AI call
        self.mock_openai.return_value.chat.completions.create.side_effect = OpenAIError(
            "AI service unavailable"
        )

        listing = Listing.objects.create(title="another job", company="another company")

        self.assertTrue(Listing.objects.filter(pk=listing.pk).exists())
        self.assertIsNone(listing.score.score)
        self.assertIsNone(listing.score.reasoning)
    
    # Test | If AI call is successful, but message is None, listing is still saved with an N/A credibility score
    def test_message_none(self):
        self.mock_openai.return_value.chat.completions.create.return_value.choices[0].message.content = None
        with self.assertRaises(TypeError):
            parse_credibility_response(self.mock_openai.return_value.chat.completions.create.return_value.choices[0].message.content)
    
    # Test | A lack of API key doesn't crash
    def test_no_key(self):
        
        # remake env as dictionary and skip API key
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        
        # patch.dict allows temporarily changing dictionary, which is what env is
        with patch.dict(os.environ, env, clear=True):
            self.mock_openai.side_effect = OpenAIError("401 - Incorrect API key provided")
            listing = Listing.objects.create(title="another job", company="another company")
            self.mock_openai.assert_called_with(api_key=None)
            self.assertTrue(Listing.objects.filter(pk=listing.pk).exists())
            self.assertIsNone(listing.score.score)
            self.assertIsNone(listing.score.reasoning)
    
    # Test | Upon creating a credibility score, is it attached to the listing?
    def test_credibility_attached(self):
        self.score = CredibilityScore.objects.get(listing=self.listing)
        self.assertEqual(self.score.listing, self.listing)
        self.assertEqual(self.score.score, self.listing.score.score)
        
    # Test | Upon an attempt to add two credibility scores to a listing, an error is thrown
    def test_only_one_cred_score(self):
        self.score = 42
        self.score2 = 43
        self.score1 = CredibilityScore.objects.get(listing=self.listing)
        with self.assertRaises(IntegrityError):
            self.score2 = CredibilityScore.objects.create(listing = self.listing, score=self.score2)
    
    # Test | Upon getting the AI response for credibility score, ensure the parsing function outputs correctly
    def test_parse_credibility_response(self):
        self.assertEqual(
            parse_credibility_response(
                "Reasons: Consistent company, clear title; Final Score: 82"
            ),
            ("Consistent company, clear title", 82),
        )
    
    # Test | Upon getting the AI response for credibility score, ensure parsing properly errors with invalid input
    def test_reject_invalid_credibility_score_input(self):
        # Too high of score
        with self.assertRaises(ValueError):
            parse_credibility_response("Reasons: Looks credible; Final Score: 101")
        
        # Too low of score
        with self.assertRaises(ValueError):
            parse_credibility_response("Reasons: This sucks bro; Final Score: -20")
        
        # Empty reasoning
        with self.assertRaises(ValueError):
            parse_credibility_response("Reasons: Final Score: 69")
        
        # Too many characters in reasoning
        with self.assertRaises(ValueError):
            parse_credibility_response("Reasons: This listing seems fascinating! The company, Shinra Corp seems like it is the most ethical company in the world, and they would do nothing wrong. You should definitely apply for their position, and enter the fabulous wondrous world of Mako mining! I need a few more characters to be over the limit. Final Score: 69")
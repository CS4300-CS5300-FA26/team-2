from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import CredibilityScore
from listings.models import Listing

import os
import random
from django.db import IntegrityError
from unittest.mock import patch

from .signals import parse_credibility_response

class AiTests(TestCase):
    
    def setUp(self):
        # Create listing for the credibility score to be attached to
        self.listing = Listing.objects.create(title="job", company="company")
        
        random.seed()
    
    # Test | Upon creating a credibility score, is it attached to the listing?
    def test_credibility_attached(self):
        self.score = CredibilityScore.objects.get(listing=self.listing)
        self.assertEqual(self.score.listing, self.listing)
        self.assertEqual(self.score.score, self.listing.score.score)
        
    # Test | Upon an attempt to add two credibility scores to a listing, an error is thrown
    def test_only_one_cred_score(self):
        self.randscore1 = random.randint(0, 100)
        self.randscore2 = random.randint(0, 100)
        self.score1 = CredibilityScore.objects.get(listing=self.listing)
        with self.assertRaises(IntegrityError):
            self.score2 = CredibilityScore.objects.create(listing = self.listing, score=self.randscore2)
    
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
            parse_credibility_response("""Reasons: This listing seems fascinating! The company, Shinra Corp seems like it is the most 
                                       ethical company in the world, and they would do nothing wrong. You should definitely apply for their 
                                       position, and enter the fabulous wondrous world of Mako mining! I need a few more characters to be over 
                                       the limit. Final Score: 69""")
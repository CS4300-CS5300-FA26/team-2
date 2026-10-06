from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import CredibilityScore
from listings.models import Listing

import random
from django.db import IntegrityError

class AiTests(TestCase):
    
    def setUp(self):        
        # Create listing for the credibility score to be attached to
        self.listing = Listing.objects.create(title="job", company="company")
        
        random.seed()
    
    # Test | Upon creating a credibility score, is it attached to the listing?
    def test_credibility_attached(self):
        self.randscore = random.randint(0, 100)
        self.score = CredibilityScore.objects.create(listing=self.listing, score=self.randscore)
        self.assertEqual(self.score.listing, self.listing)
        self.assertEqual(self.score.score, self.randscore)
        
    # Test | Upon an attempt to add two credibility scores to a listing, an error is thrown
    def test_only_one_cred_score(self):
        self.randscore1 = random.randint(0, 100)
        self.randscore2 = random.randint(0, 100)
        self.score1 = CredibilityScore.objects.create(listing = self.listing, score = self.randscore1)
        with self.assertRaises(IntegrityError):
            self.score2 = CredibilityScore.objects.create(listing = self.listing, score = self.randscore2)
from django.db import models  # noqa: F401

# CredibilityScore that represents a single number tied to a Listing
class CredibilityScore(models.Model):
    listing = models.OneToOneField("listings.Listing", on_delete=models.CASCADE, related_name="score")
    score = models.IntegerField(null=True, blank=True)
    
    # Name for the CredibilityScore object is in form of
    # "<name of listing> | <score>""
    def __str__(self):
        return f"{self.listing.title} at {self.listing.company} | {self.score}"
from django.db import models
from django.conf import settings

# Listing type that inherits from models.Model
#Tells Django this should be a database table
#Each job is a row in the table
class Listing(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    # How the listing shows uo
    def __str__(self):
        return self.title + " at " + self.company

# Bookmark class allows for extra info about saved jobs
class Bookmark(models.Model):
    #which user saved it
    #setting.AUTH allows for line to keep wroking if team mate chnges user model
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    #which job was saved
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    #when they saved it
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # a user can only bookmark the same listing once
        constraints = [
            models.UniqueConstraint(fields=["user", "listing"], name="unique_bookmark")
        ]

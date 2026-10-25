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


#Sprint 2
# US4.4: a private note on one of my saved jobs.
# A saved job (bookmark) can have MANY notes, so notes are their own table.
# Notes belong to a bookmark, and a bookmark belongs to one user,
# so only that user can ever see their notes.
class Note(models.Model):
    # which saved job this note is about.
    # related_name="notes" lets us write bookmark.notes.all()
    # CASCADE: if the bookmark is removed, its notes are removed too
    bookmark = models.ForeignKey(Bookmark, on_delete=models.CASCADE, related_name="notes")
    # what the note says
    text = models.TextField()
    # when the note was written
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # oldest note first, so they read in the order I wrote them
        ordering = ["created_at"]

    def __str__(self):
        return self.text

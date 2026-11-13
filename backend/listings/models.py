from django.db import models
from django.conf import settings

# Listing type that inherits from models.Model
# Tells Django this should be a database table
# Each job is a row in the table


class Listing(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    # Sprint 3: details for real jobs imported from the JobDataLake API.
    # All optional, so listings added by hand in admin still work.
    # the job's ID in JobDataLake, so the same job is never imported twice
    # (null for hand-added listings; unique still allows many nulls)
    external_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    # where the job is, e.g. "San Francisco, CA; Remote"
    location = models.CharField(max_length=300, blank=True, default="")
    # fully_remote, hybrid, or on_site
    remote_type = models.CharField(max_length=20, blank=True, default="")
    # the company's page for applying to this job
    apply_url = models.URLField(max_length=500, blank=True, default="")

    # How the listing shows uo
    def __str__(self):
        return self.title + " at " + self.company

# Bookmark class allows for extra info about saved jobs


class Bookmark(models.Model):
    # which user saved it
    # setting.AUTH allows for line to keep wroking if team mate chnges user model
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # which job was saved
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    # when they saved it
    created_at = models.DateTimeField(auto_now_add=True)

    # Sprint 3
    # US4.5: where I am with this application.
    # Each pair is (what's stored in the database, what people see).
    STATUS_CHOICES = [
        ("saved", "Saved"),
        ("applied", "Applied"),
        ("interviewing", "Interviewing"),
        ("offer", "Offer"),
        ("rejected", "Rejected"),
    ]
    # every saved job starts as "saved"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="saved")

    class Meta:
        # a user can only bookmark the same listing once
        constraints = [
            models.UniqueConstraint(fields=["user", "listing"], name="unique_bookmark")
        ]


# Sprint 2
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

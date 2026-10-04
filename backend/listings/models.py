from django.db import models  # noqa: F401

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

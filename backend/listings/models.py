from django.db import models


class Listing(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

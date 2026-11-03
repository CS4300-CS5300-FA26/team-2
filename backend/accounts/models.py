from django.conf import settings
from django.db import models


# US1.3: while this row exists, the user has not confirmed their email yet.
# Deleting it (after the right code is typed in) activates the account.
class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    # wrong guesses on this code, so nobody can just try all 1,000,000 codes
    attempts = models.PositiveSmallIntegerField(default=0)

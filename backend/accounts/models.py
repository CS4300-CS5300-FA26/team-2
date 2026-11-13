from django.conf import settings
from django.db import models
from django.utils import timezone


# While this row exists, the user hasn't finished signing up.
# No code yet means step 2 (profile, US1.2) isn't done; a code means step 3
# (email code, US1.3) isn't done. Deleting it (right code typed in) activates the account.
# It's in the database, so logging out and back in doesn't skip a step.
class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, blank=True)
    # wrong guesses on this code, so nobody can just try all 1,000,000 codes
    attempts = models.PositiveSmallIntegerField(default=0)
    # when the code was emailed; codes stop working 10 minutes after this
    sent_at = models.DateTimeField(default=timezone.now)

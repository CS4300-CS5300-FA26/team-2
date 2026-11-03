from django.shortcuts import redirect

from .models import EmailVerification

# pages a half-signed-up user can still reach (login, logout, the sign-up steps)
OPEN_PATHS = ("/accounts/", "/static/", "/media/")


# Someone who signed up but hasn't finished step 2 (US1.2) or step 3 (US1.3)
# gets sent back to that step from any page (/feed/, /saved/, ...).
# This is read from the database, so logging out and back in doesn't skip a step.
class ProfileStepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith(OPEN_PATHS):
            pending = EmailVerification.objects.filter(user=request.user).first()
            if pending is not None:
                return redirect("signup_verify" if pending.code else "signup_profile")
        return self.get_response(request)

from django.shortcuts import redirect

from .models import EmailVerification

# pages a half-signed-up user can still reach (login, logout, the sign-up steps)
OPEN_PATHS = ("/accounts/", "/static/", "/media/")


# Someone who signed up but hasn't finished step 2 (US1.2) or step 3 (US1.3)
# gets sent back to that step from any page (/feed/, /saved/, ...).
class ProfileStepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(OPEN_PATHS):
            # shortcut: the step 2 flag lives in the session, so logging out and back in
            # skips step 2; move it to a field on a profile model if that matters.
            if request.session.get("profile_pending"):
                return redirect("signup_profile")
            # step 3 is checked in the database, so logging out doesn't skip it
            if (
                request.user.is_authenticated
                and EmailVerification.objects.filter(user=request.user).exists()
            ):
                return redirect("signup_verify")
        return self.get_response(request)

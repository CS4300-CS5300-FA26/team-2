from django.shortcuts import redirect


# Someone who signed up but hasn't finished step 2 (US1.2) gets sent back to it
# from any page (/feed/, /saved/, ...). Login, logout and sign-up pages stay reachable.
# shortcut: the flag lives in the session, so logging out and back in skips step 2;
# move it to a field on a profile model if that matters.
class ProfileStepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get("profile_pending") and not request.path.startswith(
            ("/accounts/", "/static/", "/media/")
        ):
            return redirect("signup_profile")
        return self.get_response(request)

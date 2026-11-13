from django.http import JsonResponse

from .models import EmailVerification

# the API a half-signed-up user can still use: login, logout, me and the sign-up steps
OPEN_PATHS = ("/api/auth/", "/api/csrf/")


# Someone who signed up but hasn't finished step 2 (US1.2) or step 3 (US1.3)
# can't use the rest of the API (/api/listings/, /api/resumes/, ...). The React app
# sends them back to the step they owe; this stops anyone calling the API directly.
# It's read from the database, so logging out and back in doesn't skip a step.
class ProfileStepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if (
            request.user.is_authenticated
            and path.startswith("/api/")
            and not path.startswith(OPEN_PATHS)
            and EmailVerification.objects.filter(user=request.user).exists()
        ):
            return JsonResponse({"detail": "Finish signing up first."}, status=403)
        return self.get_response(request)

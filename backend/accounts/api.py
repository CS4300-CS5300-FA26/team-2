"""JSON auth endpoints for the React app, mounted under /api/auth/.

Errors are returned as 400 {"errors": {field_or___all__: [messages]}}.
"""
import json
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import ProfileForm, VerifyCodeForm
from .models import EmailVerification

# after this many wrong codes the code stops working (US1.3)
MAX_CODE_ATTEMPTS = 5
# a code only works for this long after it is emailed (US1.3)
CODE_LIFETIME = timedelta(minutes=10)
# at most one code email per this long, so nobody can flood an inbox (US1.3)
RESEND_COOLDOWN = timedelta(minutes=1)


def is_profile_complete(user):
    return bool(user.first_name and user.last_name and user.email)


def _user_json(user):
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        # sign-up step 2 cannot be skipped: the frontend sends users here until True
        "profile_complete": is_profile_complete(user),
        # sign-up step 3 (US1.3): False until the emailed code is entered
        "email_verified": not EmailVerification.objects.filter(user=user).exists(),
    }


def _body(request):
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _errors(form_errors):
    return JsonResponse({"errors": form_errors}, status=400)


def _not_logged_in():
    return JsonResponse({"errors": {"__all__": ["Not logged in."]}}, status=401)


@require_GET
@ensure_csrf_cookie
def csrf(request):
    # token in the body too: a cross-origin page can't read this API's cookie
    return JsonResponse({"detail": "ok", "csrfToken": get_token(request)})


@require_GET
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"user": None})
    return JsonResponse({"user": _user_json(request.user)})


@require_POST
def login_view(request):
    data = _body(request)
    user = authenticate(request, username=data.get("username"), password=data.get("password"))
    if user is None:
        return _errors({"__all__": ["Please enter a correct username and password."]})
    login(request, user)
    return JsonResponse({"user": _user_json(user)})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"user": None})


@require_POST
def signup(request):
    form = UserCreationForm(_body(request))
    if not form.is_valid():
        return _errors(form.errors)
    user = form.save()
    login(request, user)
    # remember they still owe steps 2 and 3 (ProfileStepMiddleware checks this)
    EmailVerification.objects.create(user=user)
    return JsonResponse({"user": _user_json(user)}, status=201)


@require_POST
def signup_profile(request):
    if not request.user.is_authenticated:
        return _not_logged_in()
    form = ProfileForm(_body(request), instance=request.user)
    if not form.is_valid():
        return _errors(form.errors)
    try:
        with transaction.atomic():
            user = form.save()
    except IntegrityError:
        # someone else saved the same email at the same moment; the
        # database's unique email index (migration 0003) stopped it
        return _errors({"email": ["An account with this email already exists."]})

    # accounts from before US1.3 have no row and count as verified
    pending = EmailVerification.objects.filter(user=user).first()
    if pending is not None:
        if settings.EMAIL_VERIFICATION:
            # next step: confirm the email with a code (US1.3)
            send_verification_code(user)
        else:
            pending.delete()
    return JsonResponse({"user": _user_json(user)})


# Makes a new random 6-digit code for the user and emails it to them (US1.3).
# Returns False (and sends nothing) if a code was emailed less than a minute ago.
def send_verification_code(user):
    pending = EmailVerification.objects.filter(user=user).first()
    if pending and pending.code and timezone.now() - pending.sent_at < RESEND_COOLDOWN:
        return False

    code = f"{secrets.randbelow(1000000):06d}"
    EmailVerification.objects.update_or_create(
        user=user, defaults={"code": code, "attempts": 0, "sent_at": timezone.now()}
    )
    send_mail(
        "Your Pathfinder verification code",
        f"Your Pathfinder verification code is {code}.",
        None,  # sent from DEFAULT_FROM_EMAIL
        [user.email],
    )
    return True


# Step 3 of sign-up (US1.3): the user sends the code from their email.
# The account only counts as activated once the right code is entered.
@require_POST
def signup_verify(request):
    if not request.user.is_authenticated:
        return _not_logged_in()
    pending = EmailVerification.objects.filter(user=request.user).first()
    # nothing to verify (already done)
    if pending is None:
        return JsonResponse({"user": _user_json(request.user)})
    # no code yet means step 2 isn't done
    if not pending.code:
        return _errors({"__all__": ["Finish your profile first."]})

    form = VerifyCodeForm(_body(request))
    if not form.is_valid():
        return _errors(form.errors)

    if pending.attempts >= MAX_CODE_ATTEMPTS:
        msg = "Too many wrong codes. Click Resend code to get a new one."
    elif timezone.now() - pending.sent_at > CODE_LIFETIME:
        msg = "That code has expired. Click Resend code to get a new one."
    elif form.cleaned_data["code"].strip() == pending.code:
        pending.delete()
        return JsonResponse({"user": _user_json(request.user)})
    else:
        pending.attempts += 1
        pending.save()
        if pending.attempts >= MAX_CODE_ATTEMPTS:
            msg = "Too many wrong codes. Click Resend code to get a new one."
        else:
            msg = "That code is not correct. Check your email and try again."
    return _errors({"code": [msg]})


# The "Resend code" button on step 3 (US1.3).
@require_POST
def signup_resend(request):
    if not request.user.is_authenticated:
        return _not_logged_in()
    pending = EmailVerification.objects.filter(user=request.user).first()
    if pending is None or not pending.code:
        return _errors({"__all__": ["There is no code to resend."]})
    if not send_verification_code(request.user):
        return JsonResponse({"detail": "We just sent you a code. Wait a minute before asking for another."}, status=429)
    return JsonResponse({"detail": "We emailed you a new code."})

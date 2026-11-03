import secrets
from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ProfileForm, VerifyCodeForm
from .models import EmailVerification

# after this many wrong codes the code stops working (US1.3)
MAX_CODE_ATTEMPTS = 5
# a code only works for this long after it is emailed (US1.3)
CODE_LIFETIME = timedelta(minutes=10)
# at most one code email per this long, so nobody can flood an inbox (US1.3)
RESEND_COOLDOWN = timedelta(minutes=1)


# This shows the sign-up page and creates the account when the form is sent.
# UserCreationForm checks the password against AUTH_PASSWORD_VALIDATORS
# (in settings/base.py), so a weak password gets an error instead of an account.
def signup(request):
    if request.method == "POST":
        # fill the form with what the user typed
        form = UserCreationForm(request.POST)

        if form.is_valid():
            # save the new user, then log them in right away
            user = form.save()
            login(request, user)
            # remember they still owe steps 2 and 3 (ProfileStepMiddleware checks this)
            EmailVerification.objects.create(user=user)

            # next step: fill in the profile (US1.2)
            return redirect("signup_profile")
    else:
        # first visit, so show an empty form
        form = UserCreationForm()

    # show the page (with error messages if the form wasn't valid)
    return render(request, "accounts/signup.html", {"form": form})


# Step 2 of sign-up (US1.2): the logged-in user fills in their name and email.
# It reuses the sign-up page's look, only the text changes.
@login_required
def signup_profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                # someone else saved the same email at the same moment; the
                # database's unique email index (migration 0003) stopped it
                form.add_error("email", "An account with this email already exists.")
            else:
                # next step: confirm the email with a code (US1.3)
                send_verification_code(request.user)
                return redirect("signup_verify")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/signup.html", {
        "form": form,
        "step": "Step 2 of 3",
        "heading": "Complete your profile",
        "subtitle": "Tell us a bit about yourself so your account is ready to use.",
        "button": "Finish",
    })


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


# Step 3 of sign-up (US1.3): the user types in the code from their email.
# The account only counts as activated once the right code is entered.
@login_required
def signup_verify(request):
    pending = EmailVerification.objects.filter(user=request.user).first()

    # nothing to verify (already done), so go straight to the feed
    if pending is None:
        return redirect("/feed/")
    # no code yet means step 2 isn't done
    if not pending.code:
        return redirect("signup_profile")

    # the "Resend code" button: email a fresh code and show an empty form
    status = None
    if request.method == "POST" and "resend" in request.POST:
        if send_verification_code(request.user):
            status = "We emailed you a new code."
        else:
            status = "We just sent you a code. Wait a minute before asking for another."
        form = VerifyCodeForm()
    else:
        form = VerifyCodeForm(request.POST or None)

    if request.method == "POST" and form.is_bound and form.is_valid():
        if pending.attempts >= MAX_CODE_ATTEMPTS:
            form.add_error("code", "Too many wrong codes. Click Resend code to get a new one.")
        elif timezone.now() - pending.sent_at > CODE_LIFETIME:
            form.add_error("code", "That code has expired. Click Resend code to get a new one.")
        elif form.cleaned_data["code"].strip() == pending.code:
            pending.delete()
            return redirect("/feed/")
        else:
            pending.attempts += 1
            pending.save()
            if pending.attempts >= MAX_CODE_ATTEMPTS:
                form.add_error("code", "Too many wrong codes. Click Resend code to get a new one.")
            else:
                form.add_error("code", "That code is not correct. Check your email and try again.")

    return render(request, "accounts/signup.html", {
        "form": form,
        "step": "Step 3 of 3",
        "heading": "Verify your email",
        "subtitle": f"We sent a 6-digit code to {request.user.email}.",
        "button": "Verify",
        "can_resend": True,
        "status": status,
    })

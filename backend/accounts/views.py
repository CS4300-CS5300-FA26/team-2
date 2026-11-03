import secrets

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import ProfileForm, VerifyCodeForm
from .models import EmailVerification

# after this many wrong codes we email a fresh one (US1.3)
MAX_CODE_ATTEMPTS = 5


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
            # remember they still owe step 2 (ProfileStepMiddleware checks this)
            request.session["profile_pending"] = True

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
            form.save()
            request.session.pop("profile_pending", None)
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
def send_verification_code(user):
    code = f"{secrets.randbelow(1000000):06d}"
    EmailVerification.objects.update_or_create(
        user=user, defaults={"code": code, "attempts": 0}
    )
    send_mail(
        "Your Pathfinder verification code",
        f"Your Pathfinder verification code is {code}.",
        None,  # sent from DEFAULT_FROM_EMAIL
        [user.email],
    )


# Step 3 of sign-up (US1.3): the user types in the code from their email.
# The account only counts as activated once the right code is entered.
@login_required
def signup_verify(request):
    pending = EmailVerification.objects.filter(user=request.user).first()

    # nothing to verify (already done), so go straight to the feed
    if pending is None:
        return redirect("/feed/")

    # the "Resend code" button: email a fresh code and show an empty form
    if request.method == "POST" and "resend" in request.POST:
        send_verification_code(request.user)
        form = VerifyCodeForm()
        sent_again = True
    else:
        form = VerifyCodeForm(request.POST or None)
        sent_again = False

    if request.method == "POST" and form.is_bound and form.is_valid():
        if form.cleaned_data["code"].strip() == pending.code:
            pending.delete()
            return redirect("/feed/")

        pending.attempts += 1
        if pending.attempts >= MAX_CODE_ATTEMPTS:
            send_verification_code(request.user)
            form.add_error("code", "Too many wrong codes. We emailed you a new one.")
        else:
            pending.save()
            form.add_error("code", "That code is not correct. Check your email and try again.")

    return render(request, "accounts/signup.html", {
        "form": form,
        "step": "Step 3 of 3",
        "heading": "Verify your email",
        "subtitle": f"We sent a 6-digit code to {request.user.email}.",
        "button": "Verify",
        "can_resend": True,
        "sent_again": sent_again,
    })

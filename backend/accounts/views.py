from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from .forms import ProfileForm


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
            return redirect("/feed/")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/signup.html", {
        "form": form,
        "step": "Step 2 of 2",
        "heading": "Complete your profile",
        "subtitle": "Tell us a bit about yourself so your account is ready to use.",
        "button": "Finish",
    })

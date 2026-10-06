from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


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

            # send them to the job feed
            return redirect("/feed/")
    else:
        # first visit, so show an empty form
        form = UserCreationForm()

    # show the page (with error messages if the form wasn't valid)
    return render(request, "accounts/signup.html", {"form": form})

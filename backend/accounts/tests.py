from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SignupPageTests(TestCase):

    # TEST 1: the sign-up page loads and shows the form
    def test_signup_page_loads(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign up")

    # TEST 2: a strong password creates the account, logs the user in,
    # and sends them to the profile step (US1.2)
    def test_strong_password_creates_account(self):
        response = self.client.post("/accounts/signup/", {
            "username": "newuser",
            "password1": "Tr1cky-Passw0rd!",
            "password2": "Tr1cky-Passw0rd!",
        })

        self.assertRedirects(response, "/accounts/signup/profile/")
        self.assertTrue(User.objects.filter(username="newuser").exists())

        # the profile step needs a login, so a 200 here means they were logged in
        self.assertEqual(self.client.get("/accounts/signup/profile/").status_code, 200)

    # TEST 5: a new user can't skip step 2 by going straight to the feed
    # (or any other page); after finishing step 2 the feed opens
    def test_cannot_skip_profile_step(self):
        self.client.post("/accounts/signup/", {
            "username": "newuser",
            "password1": "Tr1cky-Passw0rd!",
            "password2": "Tr1cky-Passw0rd!",
        })

        self.assertRedirects(self.client.get("/feed/"), "/accounts/signup/profile/")
        self.assertRedirects(self.client.get("/saved/"), "/accounts/signup/profile/")

        self.client.post("/accounts/signup/profile/", {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
        })
        self.assertEqual(self.client.get("/feed/").status_code, 200)

    # TEST 3: a weak password is rejected and no account is made
    def test_weak_password_is_rejected(self):
        response = self.client.post("/accounts/signup/", {
            "username": "newuser",
            "password1": "12345678",
            "password2": "12345678",
        })

        # the page shows again (no redirect) with an error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is too common")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    # TEST 4: a password that is too short is rejected
    def test_short_password_is_rejected(self):
        response = self.client.post("/accounts/signup/", {
            "username": "newuser",
            "password1": "Ab1!",
            "password2": "Ab1!",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is too short")
        self.assertFalse(User.objects.filter(username="newuser").exists())


class SignupProfileStepTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="newuser", password="Tr1cky-Passw0rd!")
        self.client.login(username="newuser", password="Tr1cky-Passw0rd!")

    # TEST 1: the profile step loads for a logged-in user
    def test_profile_step_loads(self):
        response = self.client.get("/accounts/signup/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Step 2 of 2")
        self.assertContains(response, "Complete your profile")

    # TEST 2: someone who isn't logged in is sent to the login page
    def test_profile_step_needs_login(self):
        self.client.logout()
        response = self.client.get("/accounts/signup/profile/")

        self.assertRedirects(response, "/accounts/login/?next=/accounts/signup/profile/")

    # TEST 3: filling in every field saves the profile and goes to the feed
    def test_complete_profile_is_saved(self):
        response = self.client.post("/accounts/signup/profile/", {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
        })

        self.assertRedirects(response, "/feed/")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ada")
        self.assertEqual(self.user.last_name, "Lovelace")
        self.assertEqual(self.user.email, "ada@example.com")

    # TEST 4: leaving a field empty shows an error and saves nothing
    def test_missing_field_is_rejected(self):
        response = self.client.post("/accounts/signup/profile/", {
            "first_name": "Ada",
            "last_name": "",
            "email": "ada@example.com",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "")

    # TEST 5: a badly formatted email is rejected
    def test_bad_email_is_rejected(self):
        response = self.client.post("/accounts/signup/profile/", {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "not-an-email",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address")

    # TEST 6: an email another account already uses is rejected,
    # even with different capital letters
    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username="ada", password="pw", email="ada@example.com")

        response = self.client.post("/accounts/signup/profile/", {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ADA@Example.com",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "")

    # TEST 7: saving the profile again with your own email still works
    def test_own_email_is_allowed(self):
        self.user.email = "ada@example.com"
        self.user.save()

        response = self.client.post("/accounts/signup/profile/", {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
        })

        self.assertRedirects(response, "/feed/")

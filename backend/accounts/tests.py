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
    # and sends them to the feed
    def test_strong_password_creates_account(self):
        response = self.client.post("/accounts/signup/", {
            "username": "newuser",
            "password1": "Tr1cky-Passw0rd!",
            "password2": "Tr1cky-Passw0rd!",
        })

        self.assertRedirects(response, "/feed/")
        self.assertTrue(User.objects.filter(username="newuser").exists())

        # the feed needs a login, so a 200 here means they were logged in
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

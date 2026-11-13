from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from .models import EmailVerification

User = get_user_model()
PW = "Tr1cky-Passw0rd!"


class AuthApiTests(TestCase):
    def post(self, path, data):
        return self.client.post(f"/api/auth/{path}", data, content_type="application/json")

    def test_csrf_sets_cookie(self):
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_csrf_enforced_on_login(self):
        c = Client(enforce_csrf_checks=True)
        body = {"username": "u", "password": PW}
        User.objects.create_user(username="u", password=PW)
        self.assertEqual(c.post("/api/auth/login", body, content_type="application/json").status_code, 403)
        token = c.get("/api/auth/csrf").json()["csrfToken"]
        response = c.post("/api/auth/login", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_me_logged_out_and_in(self):
        self.assertEqual(self.client.get("/api/auth/me").json(), {"user": None})
        User.objects.create_user(username="u", password=PW)
        self.client.login(username="u", password=PW)
        user = self.client.get("/api/auth/me").json()["user"]
        self.assertEqual(user["username"], "u")
        self.assertFalse(user["profile_complete"])

    def test_login_ok_and_bad(self):
        User.objects.create_user(username="u", password=PW)
        self.assertEqual(self.post("login", {"username": "u", "password": "nope"}).status_code, 400)
        response = self.post("login", {"username": "u", "password": PW})
        self.assertEqual(response.json()["user"]["username"], "u")
        self.assertIsNotNone(self.client.get("/api/auth/me").json()["user"])

    def test_logout(self):
        User.objects.create_user(username="u", password=PW)
        self.client.login(username="u", password=PW)
        self.post("logout", {})
        self.assertIsNone(self.client.get("/api/auth/me").json()["user"])

    def test_signup_creates_and_logs_in(self):
        response = self.post("signup", {"username": "new", "password1": PW, "password2": PW})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="new").exists())
        self.assertIsNotNone(self.client.get("/api/auth/me").json()["user"])

    def test_signup_weak_and_short_passwords_rejected(self):
        for pw, msg in (("12345678", "too common"), ("Ab1!", "too short")):
            response = self.post("signup", {"username": "new", "password1": pw, "password2": pw})
            self.assertEqual(response.status_code, 400)
            self.assertIn(msg, str(response.json()["errors"]["password2"]))
        self.assertFalse(User.objects.filter(username="new").exists())

    def test_profile_needs_login(self):
        self.assertEqual(self.post("signup/profile", {}).status_code, 401)

    def test_profile_saved_and_complete(self):
        User.objects.create_user(username="u", password=PW)
        self.client.login(username="u", password=PW)
        response = self.post("signup/profile", {"first_name": "Ada", "last_name": "L", "email": "ada@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["user"]["profile_complete"])

    def test_profile_missing_field_and_bad_email_rejected(self):
        user = User.objects.create_user(username="u", password=PW)
        self.client.login(username="u", password=PW)
        response = self.post("signup/profile", {"first_name": "Ada", "last_name": "", "email": "ada@example.com"})
        self.assertIn("last_name", response.json()["errors"])
        response = self.post("signup/profile", {"first_name": "Ada", "last_name": "L", "email": "nope"})
        self.assertIn("email", response.json()["errors"])
        user.refresh_from_db()
        self.assertEqual(user.first_name, "")

    def test_profile_duplicate_email_blocked(self):
        User.objects.create_user(username="a", password=PW, email="Ada@example.com")
        User.objects.create_user(username="u", password=PW)
        self.client.login(username="u", password=PW)
        response = self.post("signup/profile", {"first_name": "B", "last_name": "C", "email": "ada@example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])


class SignupStepGuardTests(TestCase):
    """US1.2/US1.3: a half-signed-up user can't use the rest of the API."""

    def post(self, path, data):
        return self.client.post(f"/api/auth/{path}", data, content_type="application/json")

    def test_cannot_skip_profile_step(self):
        self.post("signup", {"username": "new", "password1": PW, "password2": PW})
        self.assertEqual(self.client.get("/api/listings/feed/").status_code, 403)
        self.assertEqual(self.client.get("/api/listings/saved/").status_code, 403)
        # logging out and back in doesn't get around it
        self.post("logout", {})
        self.post("login", {"username": "new", "password": PW})
        self.assertEqual(self.client.get("/api/listings/feed/").status_code, 403)
        # login/me still work so the app can send them to the right step
        self.assertFalse(self.client.get("/api/auth/me").json()["user"]["email_verified"])

    def test_old_accounts_count_as_verified(self):
        User.objects.create_user(username="old", password=PW, first_name="O", last_name="L", email="old@example.com")
        self.client.login(username="old", password=PW)
        self.assertTrue(self.client.get("/api/auth/me").json()["user"]["email_verified"])
        self.assertEqual(self.client.get("/api/listings/feed/").status_code, 200)

    @override_settings(EMAIL_VERIFICATION=False)
    def test_no_email_server_skips_code_step(self):
        self.post("signup", {"username": "new", "password1": PW, "password2": PW})
        response = self.post("signup/profile", {"first_name": "Ada", "last_name": "L", "email": "ada@example.com"})
        self.assertTrue(response.json()["user"]["email_verified"])
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.client.get("/api/listings/feed/").status_code, 200)


class SignupVerifyStepTests(TestCase):

    def post(self, path, data):
        return self.client.post(f"/api/auth/{path}", data, content_type="application/json")

    def setUp(self):
        self.post("signup", {"username": "newuser", "password1": PW, "password2": PW})
        self.user = User.objects.get(username="newuser")
        # finishing step 2 sends the code
        response = self.post("signup/profile", {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"})
        self.assertFalse(response.json()["user"]["email_verified"])
        self.code = EmailVerification.objects.get(user=self.user).code
        self.wrong = "000000" if self.code != "000000" else "111111"

    # helper: pretend the last code was emailed this many minutes ago
    def age_code(self, minutes):
        EmailVerification.objects.filter(user=self.user).update(sent_at=timezone.now() - timedelta(minutes=minutes))

    def blocked(self):
        return self.client.get("/api/listings/feed/").status_code == 403

    def test_code_is_emailed(self):
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ada@example.com"])
        self.assertIn(self.code, mail.outbox[0].body)
        self.assertRegex(self.code, r"^\d{6}$")

    def test_unverified_user_is_blocked(self):
        self.assertTrue(self.blocked())
        self.client.logout()
        self.client.login(username="newuser", password=PW)
        self.assertTrue(self.blocked())

    def test_correct_code_activates_account(self):
        response = self.post("signup/verify", {"code": self.code})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["user"]["email_verified"])
        self.assertFalse(self.blocked())

    def test_wrong_code_is_rejected(self):
        response = self.post("signup/verify", {"code": self.wrong})
        self.assertEqual(response.status_code, 400)
        self.assertIn("That code is not correct", response.json()["errors"]["code"][0])
        self.assertTrue(self.blocked())

    def test_too_many_wrong_codes_locks_code(self):
        for _ in range(5):
            response = self.post("signup/verify", {"code": self.wrong})
        self.assertIn("Too many wrong codes", response.json()["errors"]["code"][0])
        response = self.post("signup/verify", {"code": self.code})
        self.assertIn("Too many wrong codes", response.json()["errors"]["code"][0])
        self.assertTrue(self.blocked())

    def test_verify_needs_login(self):
        self.client.logout()
        self.assertEqual(self.post("signup/verify", {"code": self.code}).status_code, 401)
        self.assertEqual(self.post("signup/resend", {}).status_code, 401)

    def test_resend_code(self):
        old_code = self.code
        self.age_code(2)
        response = self.post("signup/resend", {})
        self.assertEqual(response.json()["detail"], "We emailed you a new code.")
        self.assertEqual(len(mail.outbox), 2)
        new_code = EmailVerification.objects.get(user=self.user).code
        self.assertIn(new_code, mail.outbox[1].body)
        if new_code != old_code:
            self.assertEqual(self.post("signup/verify", {"code": old_code}).status_code, 400)
        self.assertEqual(self.post("signup/verify", {"code": new_code}).status_code, 200)

    def test_resend_has_cooldown(self):
        response = self.post("signup/resend", {})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Wait a minute", response.json()["detail"])
        self.assertEqual(len(mail.outbox), 1)
        # the code they already have still works
        self.assertEqual(EmailVerification.objects.get(user=self.user).code, self.code)

    def test_expired_code_is_rejected(self):
        self.age_code(11)
        response = self.post("signup/verify", {"code": self.code})
        self.assertIn("That code has expired", response.json()["errors"]["code"][0])
        self.assertTrue(self.blocked())
        self.post("signup/resend", {})
        new_code = EmailVerification.objects.get(user=self.user).code
        self.assertEqual(self.post("signup/verify", {"code": new_code}).status_code, 200)


class UniqueEmailDatabaseTests(TestCase):

    # the database itself refuses a second account with the same email (any capitals)
    def test_database_rejects_duplicate_email(self):
        User.objects.create_user(username="a", password="pw", email="ada@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="b", password="pw", email="ADA@example.com")

    # old accounts with no email don't clash with each other
    def test_blank_emails_are_allowed(self):
        User.objects.create_user(username="a", password="pw")
        User.objects.create_user(username="b", password="pw")
        self.assertEqual(User.objects.filter(email="").count(), 2)

    # if two sign-ups race past the form check, the second gets the normal error, not a crash
    def test_race_shows_form_error(self):
        User.objects.create_user(username="other", password="pw", email="ada@example.com")
        User.objects.create_user(username="newuser", password=PW)
        self.client.login(username="newuser", password=PW)
        with patch("accounts.forms.ProfileForm.clean_email", lambda form: form.cleaned_data["email"]):
            response = self.client.post(
                "/api/auth/signup/profile",
                {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"]["email"], ["An account with this email already exists."])

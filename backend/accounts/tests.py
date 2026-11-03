from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()
PW = "Tr1cky-Passw0rd!"


class AuthApiTests(TestCase):
    def post(self, path, data):
        return self.client.post(f"/api/auth/{path}", data, content_type="application/json")

    def test_csrf_sets_cookie(self):
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

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

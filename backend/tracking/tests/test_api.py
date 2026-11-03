from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from listings.models import Listing
from tracking.models import Alert, Notification

User = get_user_model()


class AlertAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a", password="pw")
        self.other = User.objects.create_user(username="b", password="pw")
        self.client.force_authenticate(self.user)

    def test_create_alert(self):
        response = self.client.post("/api/alerts/", {"keywords": "backend intern"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Alert.objects.get().user, self.user)

    def test_create_rejects_all_blank_criteria(self):
        response = self.client.post("/api/alerts/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_returns_own_alerts(self):
        Alert.objects.create(user=self.user, keywords="mine")
        Alert.objects.create(user=self.other, keywords="theirs")
        response = self.client.get("/api/alerts/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["keywords"], "mine")

    def test_pause_via_patch(self):
        alert = Alert.objects.create(user=self.user, keywords="mine")
        response = self.client.patch(f"/api/alerts/{alert.id}/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        self.assertFalse(alert.is_active)

    def test_delete(self):
        alert = Alert.objects.create(user=self.user, keywords="mine")
        response = self.client.delete(f"/api/alerts/{alert.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Alert.objects.filter(id=alert.id).exists())

    def test_edit_criteria(self):
        alert = Alert.objects.create(user=self.user, keywords="old")
        response = self.client.patch(f"/api/alerts/{alert.id}/", {"keywords": "new"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        self.assertEqual(alert.keywords, "new")

    def test_cannot_access_another_users_alert(self):
        alert = Alert.objects.create(user=self.other, keywords="theirs")
        response = self.client.get(f"/api/alerts/{alert.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_persists_notify_method_frequency_and_digest_time(self):
        response = self.client.post(
            "/api/alerts/",
            {
                "keywords": "backend",
                "notify_method": "email",
                "frequency": "daily",
                "digest_time": "17:30",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["notify_method"], "email")
        self.assertEqual(response.data["frequency"], "daily")
        self.assertEqual(response.data["digest_time"], "17:30:00")

    def test_patch_updates_frequency_and_digest_time(self):
        alert = Alert.objects.create(user=self.user, keywords="backend")
        response = self.client.patch(
            f"/api/alerts/{alert.id}/",
            {"frequency": "daily", "digest_time": "08:00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        self.assertEqual(alert.frequency, Alert.Frequency.DAILY)
        self.assertEqual(alert.digest_time.strftime("%H:%M"), "08:00")

    def test_unauthenticated_access_is_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/alerts/")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class AlertCSRFTests(APITestCase):
    """Session-authenticated requests, as the browser makes them.

    force_authenticate skips CSRF, so the tests above can't catch a missing token.
    """

    def setUp(self):
        User.objects.create_user(username="e", password="pw")
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.login(username="e", password="pw")

    def test_create_without_csrf_token_is_rejected(self):
        response = self.client.post("/api/alerts/", {"keywords": "backend"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_sets_csrf_cookie_that_allows_create(self):
        self.client.get("/api/alerts/")
        token = self.client.cookies["csrftoken"].value
        response = self.client.post(
            "/api/alerts/", {"keywords": "backend"}, format="json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="c", password="pw")
        self.other = User.objects.create_user(username="d", password="pw")
        self.client.force_authenticate(self.user)
        self.alert = Alert.objects.create(user=self.user, keywords="backend")
        self.listing = Listing.objects.create(title="Backend Intern", company="Acme")

    def test_list_only_returns_own_notifications_newest_first(self):
        older = Notification.objects.create(user=self.user, alert=self.alert, listing=self.listing)
        newer = Notification.objects.create(user=self.user, alert=self.alert, listing=self.listing)
        Notification.objects.create(
            user=self.other,
            alert=Alert.objects.create(user=self.other, keywords="x"),
            listing=self.listing,
        )
        response = self.client.get("/api/notifications/")
        ids = [row["id"] for row in response.data]
        self.assertEqual(ids, [newer.id, older.id])

    def test_cannot_mutate_notifications(self):
        notification = Notification.objects.create(user=self.user, alert=self.alert, listing=self.listing)
        response = self.client.patch(f"/api/notifications/{notification.id}/", {"read": True}, format="json")
        self.assertEqual(response.status_code, 405)

    def test_unauthenticated_access_is_rejected(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/notifications/")
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

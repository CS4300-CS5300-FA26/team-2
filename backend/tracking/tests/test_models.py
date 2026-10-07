from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from listings.models import Listing
from tracking.models import Alert, Notification

User = get_user_model()


class AlertModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jess", password="pw")

    def test_rejects_all_blank_criteria(self):
        alert = Alert(user=self.user, keywords="", location="", job_type="")
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_accepts_keywords_only(self):
        alert = Alert(user=self.user, keywords="backend intern")
        alert.full_clean()  # should not raise
        alert.save()
        self.assertEqual(alert.notify_method, Alert.NotifyMethod.IN_APP)
        self.assertEqual(alert.frequency, Alert.Frequency.INSTANT)
        self.assertEqual(alert.digest_time, time(9, 0))
        self.assertTrue(alert.is_active)


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sam", password="pw")
        self.alert = Alert.objects.create(user=self.user, keywords="backend")
        self.listing = Listing.objects.create(title="Backend Intern", company="Acme")

    def test_defaults(self):
        notification = Notification.objects.create(
            user=self.user, alert=self.alert, listing=self.listing
        )
        self.assertFalse(notification.read)
        self.assertIsNone(notification.emailed_at)
        self.assertEqual(list(self.alert.notifications.all()), [notification])

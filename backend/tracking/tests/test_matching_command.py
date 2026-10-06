from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from listings.models import Listing
from tracking.models import Alert, Notification

User = get_user_model()


class RunAlertMatchingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="e", password="pw")

    def test_creates_notification_for_keyword_match(self):
        alert = Alert.objects.create(user=self.user, keywords="backend")
        listing = Listing.objects.create(title="Backend Intern", company="Acme")
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.filter(alert=alert, listing=listing).count(), 1)

    def test_no_notification_for_non_matching_listing(self):
        Alert.objects.create(user=self.user, keywords="backend")
        Listing.objects.create(title="Frontend Intern", company="Acme")
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.count(), 0)

    def test_paused_alert_is_skipped(self):
        Alert.objects.create(user=self.user, keywords="backend", is_active=False)
        Listing.objects.create(title="Backend Intern", company="Acme")
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.count(), 0)

    def test_rerun_does_not_duplicate_notification(self):
        alert = Alert.objects.create(user=self.user, keywords="backend")
        Listing.objects.create(title="Backend Intern", company="Acme")
        call_command("run_alert_matching")
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.filter(alert=alert).count(), 1)

    def test_one_bad_alert_does_not_abort_others(self):
        from unittest.mock import patch

        # created first, so it's processed first (default queryset order is by pk)
        # and is the one whose match_alert call raises below.
        Alert.objects.create(user=self.user, keywords="frontend")
        good_alert = Alert.objects.create(user=self.user, keywords="backend")
        listing = Listing.objects.create(title="Backend Intern", company="Acme")

        from tracking.management.commands import run_alert_matching as cmd_module

        original = cmd_module.match_alert
        calls = {"n": 0}

        def flaky_match(alert):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("boom")
            return original(alert)

        with patch("tracking.management.commands.run_alert_matching.match_alert", side_effect=flaky_match):
            call_command("run_alert_matching")

        self.assertEqual(Notification.objects.filter(alert=good_alert, listing=listing).count(), 1)

    def test_widened_alert_rematches_previously_unmatched_older_listing(self):
        # regression test for the cutoff-bug: a Listing created before another
        # Listing that later got notified must still be re-evaluated once the
        # alert's criteria widen to match it.
        alert = Alert.objects.create(user=self.user, keywords="backend")
        old_listing = Listing.objects.create(title="Frontend Intern", company="Acme")  # no match yet
        new_listing = Listing.objects.create(title="Backend Intern", company="Acme")  # matches, becomes "latest"
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.filter(alert=alert, listing=new_listing).count(), 1)
        self.assertEqual(Notification.objects.filter(alert=alert, listing=old_listing).count(), 0)

        alert.keywords = "intern"  # widen criteria to now match old_listing too
        alert.save()
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.filter(alert=alert, listing=old_listing).count(), 1)

    def test_location_only_alert_matches_nothing_until_location_matching_lands(self):
        Alert.objects.create(user=self.user, location="Denver")  # no keywords
        Listing.objects.create(title="Backend Intern", company="Acme")
        call_command("run_alert_matching")
        self.assertEqual(Notification.objects.count(), 0)


class InstantEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="f", password="pw", email="f@example.com")

    def test_instant_email_alert_sends_one_email_per_match(self):
        from django.core import mail

        Alert.objects.create(
            user=self.user, keywords="backend", notify_method=Alert.NotifyMethod.EMAIL
        )
        Listing.objects.create(title="Backend Intern", company="Acme")
        call_command("run_alert_matching")
        self.assertEqual(len(mail.outbox), 1)
        notification = Notification.objects.get()
        self.assertIsNotNone(notification.emailed_at)

    def test_in_app_alert_sends_no_email(self):
        from django.core import mail

        Alert.objects.create(user=self.user, keywords="backend")  # default in_app
        Listing.objects.create(title="Backend Intern", company="Acme")
        call_command("run_alert_matching")
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_leaves_notification_retryable(self):
        from unittest.mock import patch

        Alert.objects.create(
            user=self.user, keywords="backend", notify_method=Alert.NotifyMethod.EMAIL
        )
        Listing.objects.create(title="Backend Intern", company="Acme")
        with patch(
            "tracking.management.commands.run_alert_matching.send_mail",
            side_effect=RuntimeError("smtp down"),
        ):
            call_command("run_alert_matching")
        notification = Notification.objects.get()
        self.assertIsNone(notification.emailed_at)


class DailyDigestTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="g", password="pw", email="g@example.com")

    def _freeze_hour(self, hour):
        from unittest.mock import patch

        frozen = timezone.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        return patch(
            "tracking.management.commands.run_alert_matching.timezone.now", return_value=frozen
        )

    def test_daily_alert_does_not_email_outside_digest_hour(self):
        from datetime import time

        from django.core import mail

        Alert.objects.create(
            user=self.user, keywords="backend",
            notify_method=Alert.NotifyMethod.EMAIL,
            frequency=Alert.Frequency.DAILY, digest_time=time(9, 0),
        )
        Listing.objects.create(title="Backend Intern", company="Acme")
        with self._freeze_hour(14):
            call_command("run_alert_matching")
        self.assertEqual(len(mail.outbox), 0)
        notification = Notification.objects.get()
        self.assertIsNone(notification.emailed_at)

    def test_daily_alert_batches_matches_into_one_email_at_digest_hour(self):
        from datetime import time

        from django.core import mail

        Alert.objects.create(
            user=self.user, keywords="backend",
            notify_method=Alert.NotifyMethod.EMAIL,
            frequency=Alert.Frequency.DAILY, digest_time=time(9, 0),
        )
        Listing.objects.create(title="Backend Intern", company="Acme")
        Listing.objects.create(title="Backend Engineer", company="Globex")
        with self._freeze_hour(9):
            call_command("run_alert_matching")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Notification.objects.filter(emailed_at__isnull=False).count(), 2)

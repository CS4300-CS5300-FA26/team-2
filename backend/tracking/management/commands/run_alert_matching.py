import logging

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from listings.models import Listing
from tracking.models import Alert, Notification

logger = logging.getLogger(__name__)


def match_alert(alert):
    """Return Listings not yet notified for this alert, filtered by keywords.

    ponytail: location/job_type matching deferred, wire in once Listing
    gains those fields (see docs/architecture/2026-10-05-alerts-design.md).
    Until then, an alert with no keywords matches nothing rather than
    matching every listing (location/job_type can't be verified yet).
    """
    if not alert.keywords:
        return []
    return list(
        Listing.objects.exclude(notifications__alert=alert).filter(
            Q(title__icontains=alert.keywords) | Q(company__icontains=alert.keywords)
        )
    )


def send_notification_email(user, notifications):
    listing_lines = "\n".join(f"- {n.listing.title} at {n.listing.company}" for n in notifications)
    send_mail(
        subject="New job listings matching your alert",
        message=f"New listings:\n{listing_lines}",
        from_email=None,
        recipient_list=[user.email],
    )


class Command(BaseCommand):
    help = "Match active alerts against new listings and create/send notifications."

    def handle(self, *args, **options):
        now = timezone.now()
        for alert in Alert.objects.filter(is_active=True):
            try:
                matches = match_alert(alert)
                for listing in matches:
                    Notification.objects.create(user=alert.user, alert=alert, listing=listing)
            except Exception:
                logger.exception("Alert matching failed for alert id=%s", alert.id)
                continue

            if alert.notify_method != Alert.NotifyMethod.EMAIL:
                continue

            try:
                if alert.frequency == Alert.Frequency.INSTANT:
                    self._send_instant(alert, now)
                elif alert.frequency == Alert.Frequency.DAILY and now.hour == alert.digest_time.hour:
                    self._send_digest(alert, now)
            except Exception:
                logger.exception("Email send failed for alert id=%s", alert.id)

    def _send_instant(self, alert, now):
        pending = Notification.objects.filter(alert=alert, emailed_at__isnull=True)
        for notification in pending:
            send_notification_email(alert.user, [notification])
            notification.emailed_at = now
            notification.save(update_fields=["emailed_at"])

    def _send_digest(self, alert, now):
        pending = list(Notification.objects.filter(alert=alert, emailed_at__isnull=True))
        if not pending:
            return
        send_notification_email(alert.user, pending)
        Notification.objects.filter(id__in=[n.id for n in pending]).update(emailed_at=now)
        alert.last_digest_sent_at = now
        alert.save(update_fields=["last_digest_sent_at"])

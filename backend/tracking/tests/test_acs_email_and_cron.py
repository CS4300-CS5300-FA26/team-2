from unittest import mock

from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import SimpleTestCase, TestCase, override_settings

from pathfinder.acs_email import AcsEmailBackend


@override_settings(ACS_EMAIL_ENDPOINT="https://x.unitedstates.communication.azure.com", DEFAULT_FROM_EMAIL="DoNotReply@x.azurecomm.net")
class AcsEmailBackendTests(SimpleTestCase):
    def _send(self, message, fail_silently=False):
        with mock.patch("pathfinder.acs_email.EmailClient") as client, mock.patch("pathfinder.acs_email.DefaultAzureCredential"):
            backend = AcsEmailBackend(fail_silently=fail_silently)
            return backend.send_messages([message]), client.return_value.begin_send

    def test_sends_payload_with_default_sender(self):
        message = mail.EmailMessage("Subj", "Body", None, ["a@example.com"])
        sent, begin_send = self._send(message)
        self.assertEqual(sent, 1)
        payload = begin_send.call_args.args[0]
        self.assertEqual(payload["senderAddress"], "DoNotReply@x.azurecomm.net")
        self.assertEqual(payload["recipients"], {"to": [{"address": "a@example.com"}]})
        self.assertEqual(payload["content"], {"subject": "Subj", "plainText": "Body"})

    def test_html_alternative_is_included(self):
        message = EmailMultiAlternatives("S", "plain", None, ["a@example.com"])
        message.attach_alternative("<b>hi</b>", "text/html")
        _, begin_send = self._send(message)
        self.assertEqual(begin_send.call_args.args[0]["content"]["html"], "<b>hi</b>")

    def test_errors_raise_unless_fail_silently(self):
        message = mail.EmailMessage("S", "B", None, ["a@example.com"])
        with mock.patch("pathfinder.acs_email.EmailClient") as client, mock.patch("pathfinder.acs_email.DefaultAzureCredential"):
            client.return_value.begin_send.side_effect = RuntimeError("boom")
            with self.assertRaises(RuntimeError):
                AcsEmailBackend().send_messages([message])
            self.assertEqual(AcsEmailBackend(fail_silently=True).send_messages([message]), 0)


class RunAlertsEndpointTests(TestCase):
    url = "/api/internal/run-alerts/"

    @override_settings(ALERTS_CRON_TOKEN="")
    def test_disabled_without_token(self):
        self.assertEqual(self.client.post(self.url).status_code, 404)

    @override_settings(ALERTS_CRON_TOKEN="@Microsoft.KeyVault(VaultName=v;SecretName=s)")
    def test_unresolved_key_vault_reference_is_not_a_valid_token(self):
        response = self.client.post(self.url, headers={"Authorization": "Bearer @Microsoft.KeyVault(VaultName=v;SecretName=s)"})
        self.assertEqual(response.status_code, 404)

    @override_settings(ALERTS_CRON_TOKEN="s3cret")
    def test_wrong_or_missing_token_is_forbidden(self):
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, headers={"Authorization": "Bearer nope"}).status_code, 403)

    @override_settings(ALERTS_CRON_TOKEN="s3cret")
    def test_valid_token_runs_matching(self):
        with mock.patch("tracking.views.call_command") as run:
            response = self.client.post(self.url, headers={"Authorization": "Bearer s3cret"})
        self.assertEqual(response.status_code, 200)
        run.assert_called_once_with("run_alert_matching")

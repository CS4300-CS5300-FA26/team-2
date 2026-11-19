"""Django email backend that sends through Azure Communication Services Email.

Auth is the Web App's managed identity (DefaultAzureCredential), the same way
media storage authenticates in prod.py, so no connection string or key exists.
Selected in prod.py when ACS_EMAIL_ENDPOINT is set.
"""
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class AcsEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = EmailClient(settings.ACS_EMAIL_ENDPOINT, DefaultAzureCredential())
        return self._client

    @staticmethod
    def _payload(message):
        recipients = {"to": [{"address": a} for a in message.to]}
        if message.cc:
            recipients["cc"] = [{"address": a} for a in message.cc]
        if message.bcc:
            recipients["bcc"] = [{"address": a} for a in message.bcc]
        content = {"subject": message.subject, "plainText": message.body}
        for body, mimetype in getattr(message, "alternatives", []):
            if mimetype == "text/html":
                content["html"] = body
        return {
            "senderAddress": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "recipients": recipients,
            "content": content,
        }

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            if not message.recipients():
                continue
            try:
                # begin_send returns once ACS accepts the message; delivery is async, so don't wait on it
                self._get_client().begin_send(self._payload(message))
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

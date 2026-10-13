import warnings

from azure.identity import DefaultAzureCredential

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")  # raises if missing, no insecure fallback in prod

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Frontend and backend are separate App Service origins (no shared nginx
# gateway in this deploy), so the session/CSRF cookies the frontend's fetch
# calls rely on have to be sent cross-site. CORS_ALLOW_CREDENTIALS plus
# SameSite=None/Secure is what makes the browser actually attach them.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True

# Without SMTP config, alert emails are written to the server log instead of
# sent, so a deploy missing these variables still boots. In-app alerts are unaffected.
if env("EMAIL_HOST", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER or "webmaster@localhost")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    warnings.warn(
        "EMAIL_HOST is not set; alert emails will be logged, not sent. To send them, set "
        "EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD and DEFAULT_FROM_EMAIL "
        "(see README: Deployment settings)."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") # Trust the HTTPS header sent by our Railway Nginx gateway

# Media uploads (resumes) go to the real Azure Storage Account in prod,
# not the local filesystem. Auth is via the backend Web App's
# system-assigned managed identity (DefaultAzureCredential, resolved via
# IMDS at runtime), not an account key -- the Storage Account's network
# rules only allow the App Service subnet anyway, and granting
# "Storage Blob Data Contributor" to the identity (infra/terraform) means
# no key ever needs to exist. django-storages has no single
# AZURE_USE_DEFAULT_CREDENTIAL flag; passing a DefaultAzureCredential
# instance as AZURE_TOKEN_CREDENTIAL is the current documented way.
AZURE_ACCOUNT_NAME = env("AZURE_STORAGE_ACCOUNT_NAME", default="stpathfinderprodmedia")
AZURE_CONTAINER = env("AZURE_STORAGE_CONTAINER", default="media")
AZURE_TOKEN_CREDENTIAL = DefaultAzureCredential()

# Django 5.1 removed DEFAULT_FILE_STORAGE in favor of STORAGES; staticfiles
# entry is unchanged from Django's default (whitenoise's middleware serves
# collected static files regardless of which storage class collectstatic uses).
STORAGES = {
    "default": {"BACKEND": "storages.backends.azure_storage.AzureStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Sentry: only initialize with a real DSN (same non-empty-guard pattern as
# EMAIL_HOST above). Set via Key Vault (infra/terraform/app_service.tf's
# SENTRY_DSN app setting), so this is a no-op until that secret exists.
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
        # Ships stdlib logging.warning()+ as Sentry Logs, no extra code.
        enable_logs=True,
    )

# Honeybadger cron check-in ID for run_alert_matching (see that command for
# the actual ping). Not set yet -- same situation as SENTRY_DSN.
HONEYBADGER_CHECKIN_ID = env("HONEYBADGER_CHECKIN_ID", default="")

import warnings

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")  # raises if missing — no insecure fallback in prod

# The browser only ever talks to the web app, which proxies /api etc. to this backend
# (frontend/server.mjs) and forwards the web hostname as X-Forwarded-Host, so both names
# must be allowed. Env vars override these defaults.
_AZURE_HOSTS = ["app-pathfinder-prod-web.azurewebsites.net", "app-pathfinder-prod-api.azurewebsites.net"]
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=_AZURE_HOSTS)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[f"https://{h}" for h in _AZURE_HOSTS])
USE_X_FORWARDED_HOST = True  # safe: ALLOWED_HOSTS still validates the forwarded host
SESSION_COOKIE_SECURE = True
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

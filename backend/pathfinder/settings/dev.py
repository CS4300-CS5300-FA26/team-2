from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["*"]


# lets the DevEdu app link (https) log in without a CSRF error
CSRF_TRUSTED_ORIGINS = [
    "https://*.devedu.io",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

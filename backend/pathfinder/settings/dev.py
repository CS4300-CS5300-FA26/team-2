from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

ALLOWED_HOSTS = ["*"]


# lets the DevEdu app link (https) log in without a CSRF error
CSRF_TRUSTED_ORIGINS = ["https://*.devedu.io"]

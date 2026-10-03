from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")  # raises if missing — no insecure fallback in prod

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

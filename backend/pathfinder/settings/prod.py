from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")  # raises if missing — no insecure fallback in prod

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[]) 


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") # Trust the HTTPS header sent by our Railway Nginx gateway

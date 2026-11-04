from django.urls import path

from . import api

urlpatterns = [
    path("csrf", api.csrf),
    path("me", api.me),
    path("login", api.login_view),
    path("logout", api.logout_view),
    path("signup", api.signup),
    path("signup/profile", api.signup_profile),
    path("signup/verify", api.signup_verify),
    path("signup/resend", api.signup_resend),
]

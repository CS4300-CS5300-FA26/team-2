"""JSON auth endpoints for the React app, mounted under /api/auth/.

Errors are returned as 400 {"errors": {field_or___all__: [messages]}}.
"""
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import ProfileForm


def _user_json(user):
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        # sign-up step 2 cannot be skipped: the frontend sends users here until True
        "profile_complete": bool(user.first_name and user.last_name and user.email),
    }


def _body(request):
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _errors(form_errors):
    return JsonResponse({"errors": form_errors}, status=400)


@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"detail": "ok"})


@require_GET
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"user": None})
    return JsonResponse({"user": _user_json(request.user)})


@require_POST
def login_view(request):
    data = _body(request)
    user = authenticate(request, username=data.get("username"), password=data.get("password"))
    if user is None:
        return _errors({"__all__": ["Please enter a correct username and password."]})
    login(request, user)
    return JsonResponse({"user": _user_json(user)})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"user": None})


@require_POST
def signup(request):
    form = UserCreationForm(_body(request))
    if not form.is_valid():
        return _errors(form.errors)
    user = form.save()
    login(request, user)
    return JsonResponse({"user": _user_json(user)}, status=201)


@require_POST
def signup_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": {"__all__": ["Not logged in."]}}, status=401)
    form = ProfileForm(_body(request), instance=request.user)
    if not form.is_valid():
        return _errors(form.errors)
    return JsonResponse({"user": _user_json(form.save())})

"""JSON API for the job feed and saved jobs (session auth, 401 JSON when logged out)."""
import json
from accounts.api import is_profile_complete
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Bookmark, Listing, Note


def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        if not is_profile_complete(request.user):
            return JsonResponse({"detail": "Complete your profile first."}, status=403)
        return view(request, *args, **kwargs)

    return wrapper


def _listing(listing, saved):
    score = getattr(listing, "score", None)  # missing reverse one-to-one -> None
    has_score = score is not None and score.score is not None
    return {
        "id": listing.id,
        "title": listing.title,
        "company": listing.company,
        "saved": saved,
        "score": score.score if has_score else None,
        "reasoning": (score.reasoning or "") if has_score else "",
    }


@api_login_required
@require_http_methods(["GET"])
def feed(request):
    saved_ids = set(Bookmark.objects.filter(user=request.user).values_list("listing_id", flat=True))
    listings = Listing.objects.select_related("score").order_by("-created_at")
    return JsonResponse({"listings": [_listing(l, l.id in saved_ids) for l in listings]})


@api_login_required
@require_http_methods(["POST"])
def save_bookmark(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    Bookmark.objects.get_or_create(user=request.user, listing=listing)  # idempotent
    return JsonResponse({"id": listing.id, "saved": True})


@api_login_required
@require_http_methods(["POST"])
def remove_bookmark(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    Bookmark.objects.filter(user=request.user, listing=listing).delete()  # idempotent
    return JsonResponse({"id": listing.id, "saved": False})


@api_login_required
@require_http_methods(["GET"])
def saved_jobs(request):
    bookmarks = (
        Bookmark.objects.filter(user=request.user)
        .select_related("listing", "listing__score")
        .prefetch_related("notes")
        .order_by("-created_at")
    )
    out = []
    for b in bookmarks:
        item = _listing(b.listing, True)
        item["notes"] = [{"id": n.id, "text": n.text} for n in b.notes.all()]
        out.append(item)
    return JsonResponse({"listings": out})


@api_login_required
@require_http_methods(["POST"])
def add_note(request, listing_id):
    # 404 unless it's MY bookmark, so nobody can note someone else's save
    bookmark = get_object_or_404(Bookmark, user=request.user, listing_id=listing_id)
    try:
        text = str(json.loads(request.body or b"{}").get("note", "")).strip()
    except (ValueError, AttributeError):
        text = ""
    if not text:
        return JsonResponse({"detail": "Note cannot be empty."}, status=400)
    note = Note.objects.create(bookmark=bookmark, text=text)
    return JsonResponse({"id": note.id, "text": note.text}, status=201)


@api_login_required
@require_http_methods(["DELETE"])
def delete_note(request, note_id):
    # only notes on MY bookmarks; others 404
    get_object_or_404(Note, id=note_id, bookmark__user=request.user).delete()
    return JsonResponse({"id": note_id, "deleted": True})

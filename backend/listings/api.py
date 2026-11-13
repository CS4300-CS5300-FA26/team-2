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
        # Sprint 3: details from imported JobDataLake jobs (empty for hand-added ones)
        "location": listing.location,
        "remote_type": listing.remote_type,
        "apply_url": listing.apply_url,
        "saved": saved,
        "score": score.score if has_score else None,
        "reasoning": (score.reasoning or "") if has_score else "",
    }


# US3.3: ?sort_by=... choices -> the model field to order by
SORT_FIELDS = {
    "date-desc": "-created_at",
    "date-asc": "created_at",
    "score-desc": "-score__score",
    "score-asc": "score__score",
}


@api_login_required
@require_http_methods(["GET"])
def feed(request):
    # US3.3: optional ?sort_by=date-desc|date-asc|score-desc|score-asc
    #        and ?min_score=0..100&max_score=0..100 (both ends included).
    # With no query string the feed is unchanged (newest first, unscored included).
    sort_by = request.GET.get("sort_by", "date-desc")
    if sort_by not in SORT_FIELDS:
        return JsonResponse({"detail": "Invalid sort_by."}, status=400)

    listings = Listing.objects.select_related("score")

    if "min_score" in request.GET or "max_score" in request.GET:
        try:
            min_score = int(request.GET.get("min_score", 0))
            max_score = int(request.GET.get("max_score", 100))
        except ValueError:
            return JsonResponse({"detail": "Scores must be whole numbers."}, status=400)
        if not (0 <= min_score <= max_score <= 100):
            return JsonResponse({"detail": "Score range must satisfy 0 <= min <= max <= 100."}, status=400)
        listings = listings.filter(score__score__gte=min_score, score__score__lte=max_score)

    listings = listings.order_by(SORT_FIELDS[sort_by])
    saved_ids = set(Bookmark.objects.filter(user=request.user).values_list("listing_id", flat=True))
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

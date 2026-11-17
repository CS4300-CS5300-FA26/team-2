"""JSON API for the job feed and saved jobs (session auth, 401 JSON when logged out)."""
import json
from accounts.api import is_profile_complete
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import F

from .models import Bookmark, Listing, Note, Report

from django.utils import timezone   # So that reports record when they were made

# Sprint 3
# the status names a saved job can have: saved, applied, interviewing, offer, rejected
STATUSES = [value for value, label in Bookmark.STATUS_CHOICES]

# Sprint 3
# The reasons that can be given for a listing report
REPORT_REASONS = {"fake", "inappropriate", "harmful-or-illegal"}


# Sprint 3: one note as JSON, including when it was written.
# isoformat() turns the date into text like "2026-11-09T19:10:00+00:00",
# which the React page turns into "Nov 9, 2026, 12:10 PM" in your own time zone.
def _note(note):
    return {"id": note.id, "text": note.text, "created_at": note.created_at.isoformat()}


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


# Connect what front-end sends for sorting with what django calls it
SORT_FIELDS = {
    "date-desc": "-created_at",
    "date-asc": "created_at",
    "score-desc": F("score__score").desc(nulls_last=True),
    "score-asc": F("score__score").asc(nulls_last=True),
}


@api_login_required
@require_http_methods(["GET"])
def feed(request):
    # Get sort w/ date-desc being default
    sort_by = request.GET.get("sort_by", "date-desc")
    if sort_by not in SORT_FIELDS:
        return JsonResponse({"detail": "Invalid sort_by."}, status=400)
    listings = Listing.objects.select_related("score").exclude(
        reports__user=request.user.get_username()
    )

    # Filter by score
    if "min_score" in request.GET or "max_score" in request.GET:
        try:
            min_score = int(request.GET.get("min_score", 0))
            max_score = int(request.GET.get("max_score", 100))
        except ValueError:
            return JsonResponse({"detail": "Scores must be whole numbers."}, status=400)
        if not (0 <= min_score <= max_score <= 100):
            return JsonResponse({"detail": "Score range must satisfy 0 <= min <= max <= 100."}, status=400)
        # Prevent unscored from not appearing when not filtered
        if not (min_score == 0 and max_score == 100):
            listings = listings.filter(score__score__gte=min_score, score__score__lte=max_score)

    # Order listings by the sort fields
    listings = listings.order_by(SORT_FIELDS[sort_by])

    saved_ids = set(Bookmark.objects.filter(user=request.user).values_list("listing_id", flat=True))
    return JsonResponse({"listings": [_listing(listing, listing.id in saved_ids) for listing in listings]})


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

    # Sprint 3
    # US4.6: /api/listings/saved/?status=applied shows only "applied" jobs.
    # No ?status= means show every saved job.
    status = request.GET.get("status", "")
    if status:
        if status not in STATUSES:
            return JsonResponse({"detail": "Unknown status."}, status=400)
        bookmarks = bookmarks.filter(status=status)

    out = []
    for b in bookmarks:
        item = _listing(b.listing, True)
        # Sprint 3: each note also sends when it was written
        item["notes"] = [_note(n) for n in b.notes.all()]
        # Sprint 3 (US4.5): where I am with this application
        item["status"] = b.status
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
    # Sprint 3: send the date and time too, so the page can show it right away
    return JsonResponse(_note(note), status=201)


@api_login_required
@require_http_methods(["DELETE"])
def delete_note(request, note_id):
    # only notes on MY bookmarks; others 404
    get_object_or_404(Note, id=note_id, bookmark__user=request.user).delete()
    return JsonResponse({"id": note_id, "deleted": True})


# Sprint 3
# US4.5: set the status of one of my saved jobs.
# The page sends {"status": "applied"} to /api/listings/<id>/status/
@api_login_required
@require_http_methods(["POST"])
def set_status(request, listing_id):
    # 404 unless it's MY saved job, so nobody can change someone else's
    bookmark = get_object_or_404(Bookmark, user=request.user, listing_id=listing_id)

    # read the new status from the request (empty if the body is broken)
    try:
        status = str(json.loads(request.body or b"{}").get("status", ""))
    except (ValueError, AttributeError):
        status = ""

    # only the five allowed statuses can be saved
    if status not in STATUSES:
        return JsonResponse({"detail": "Unknown status."}, status=400)

    bookmark.status = status
    bookmark.save()
    return JsonResponse({"id": listing_id, "status": bookmark.status})


# Spring 3
# US3.4: Add report to database
@api_login_required
@require_http_methods(["POST"])
def report_listing(request, listing_id):
    # Try to get the listing
    listing = get_object_or_404(Listing, id=listing_id)
    
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON."}, status=400)
    
    reason = payload.get("reason") if isinstance(payload, dict) else None
    if not isinstance(reason, str) or reason not in REPORT_REASONS:
        return JsonResponse({"detail": "Invalid report reason."}, status=400)
    
    report = Report.objects.create(
        user=request.user.get_username(),
        time=timezone.now(),
        listing=listing,
        reportReason=reason,
    )
    return JsonResponse({"id": report.id}, status=201)
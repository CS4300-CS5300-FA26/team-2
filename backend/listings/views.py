from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Bookmark, Listing


# This shows the job feed page.
# You have to be logged in, because bookmarks belong to a user.
# If you're not logged in, Django sends you to LOGIN_URL (set in settings/base.py)
@login_required
def feed(request):
    # get all the listings, newest first
    listings = Listing.objects.select_related("score").order_by("-created_at")

    # make a list of the ids of listings this user bookmarked
    saved_ids = []
    for bookmark in Bookmark.objects.filter(user=request.user):
        saved_ids.append(bookmark.listing_id)

    # send the listings and saved ids to the template
    return render(request, "listings/feed.html", {
        "listings": listings,
        "saved_ids": saved_ids,
    })


# This runs when someone clicks the EMPTY bookmark (to save it).
# require_POST means only a form submit can do this, not just visiting the address.
@login_required
@require_POST
def save_bookmark(request, listing_id):
    # find the listing they clicked on (404 page if it doesn't exist)
    listing = get_object_or_404(Listing, id=listing_id)

    # get_or_create only makes a new bookmark if there isn't one already,
    # so clicking twice (or a double click) still leaves it saved
    Bookmark.objects.get_or_create(user=request.user, listing=listing)

    # send them back to the feed page
    return redirect("/feed/")


# This runs when someone clicks the FILLED bookmark (to remove it).
@login_required
@require_POST
def remove_bookmark(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    # delete this user's bookmark for this listing.
    # if it's already gone, this just does nothing, so clicking twice is fine
    Bookmark.objects.filter(user=request.user, listing=listing).delete()

    return redirect("/feed/")

#Sprint 1
# Saved Jobs page: shows every job the logged-in user bookmarked
@login_required  # not logged in? send them to the login page
def saved_jobs(request):
    # get only the listings that THIS user bookmarked,
    # newest bookmark first
    listings = Listing.objects.filter(bookmark__user=request.user).order_by("-bookmark__created_at")

    # send those listings to the saved_jobs.html page
    return render(request, "listings/saved_jobs.html", {"listings": listings})

@login_required
@require_POST
def apply_filters(request):
    sort_choice = request.POST.get("sort_by")
    sort_fields = {
        "date-desc": "-created_at",
        "date-asc": "created_at",
        "score-desc": "-score__score",
        "score-asc": "score__score",
    }
    
    # Ensure sort choice is valid
    if sort_choice not in sort_fields:
        return HttpResponseBadRequest("Bad choice")
    
    try:
        min_score = int(request.POST.get("min_score"))
        max_score = int(request.POST.get("max_score"))
    except (KeyError, ValueError):
        return HttpResponseBadRequest("Bad choice")
    
    # TODO: feed.html itself doesn't stop you from having min > max, only this does, so fix that when I have time
    if not (0 <= min_score <= max_score <= 100):
        return HttpResponseBadRequest("Bad choice")
    
    # Redo the feed thing cause i dont wanna touch nicole's code if i can help it, plus that would require adding parameters to feed
    listings = Listing.objects.select_related("score").filter(
        score__score__gte = min_score,
        score__score__lte = max_score,
    ).order_by(sort_fields[sort_choice])
    saved_ids = Bookmark.objects.filter(user=request.user).values_list("listing_id", flat=True)
    return render(request, "listings/feed.html", {
        "listings": listings,
        "saved_ids": saved_ids,
        "sort_choice": sort_choice,
        "min_score": min_score,
        "max_score": max_score,
    })
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Bookmark, Listing


# This shows the job feed page.
# You have to be logged in, because bookmarks belong to a user.
# If you're not logged in, Django sends you to LOGIN_URL (set in settings/base.py)
@login_required
def feed(request):
    # get all the listings, newest first
    listings = Listing.objects.all().order_by("-created_at")

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

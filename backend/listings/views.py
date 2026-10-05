from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Bookmark, Listing


# This shows the job feed page.
# You have to be logged in, because bookmarks belong to a user.
#URL may change once login page is official
@login_required(login_url="/admin/login/")
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


# This runs when someone clicks a bookmark button.
# If the listing is saved, it unsaves it. If it's not saved, it saves it.
@login_required(login_url="/admin/login/")
def toggle_bookmark(request, listing_id):
    if request.method == "POST":
        # find the listing they clicked on
        listing = get_object_or_404(Listing, id=listing_id)

        # check if this user already bookmarked it
        bookmark = Bookmark.objects.filter(user=request.user, listing=listing).first()

        if bookmark:
            # already saved, so remove it
            bookmark.delete()
        else:
            # not saved yet, so save it
            Bookmark.objects.create(user=request.user, listing=listing)

    # send them back to the feed page
    return redirect("/feed/")

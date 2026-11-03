from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Bookmark, Listing, Note


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
    
    # US4.3: the Remove button on the Saved Jobs page sends next="saved",
    # so send them back to Saved Jobs instead of the feed
    if request.POST.get("next") == "saved":
        return redirect("/saved/")

    return redirect("/feed/")

#Sprint 1
# Saved Jobs page: shows every job the logged-in user bookmarked
@login_required  # not logged in? send them to the login page
def saved_jobs(request):
    # US4.4: start from MY bookmarks, so we can also show my notes.
    # prefetch_related("notes") loads all the notes at once (faster)
    bookmarks = (
        Bookmark.objects.filter(user=request.user)
        .select_related("listing")
        .prefetch_related("notes")
        .order_by("-created_at")
    )

    # make a list of the saved jobs, and attach my notes to each one
    listings = []
    for bookmark in bookmarks:
        listing = bookmark.listing
        listing.my_notes = bookmark.notes.all()
        listings.append(listing)

    # send those listings to the saved_jobs.html page
    return render(request, "listings/saved_jobs.html", {"listings": listings})


#Sprint 2
# US4.4: add a new private note to one of my saved jobs
@login_required  # not logged in? send them to the login page
@require_POST    # only the form can add a note, not just visiting the address
def add_note(request, listing_id):
    # find MY bookmark for this job.
    # if I haven't saved this job, this gives a 404 page,
    # so nobody can add a note to someone else's bookmark
    bookmark = get_object_or_404(Bookmark, user=request.user, listing_id=listing_id)

    # get the text from the form (empty if missing) and remove extra spaces
    text = request.POST.get("note", "").strip()

    # only save it if they actually typed something
    if text:
        Note.objects.create(bookmark=bookmark, text=text)

    # go back to the Saved Jobs page
    return redirect("/saved/")


# US4.4: delete one of my notes (the little x)
@login_required
@require_POST    # only the x button can delete, not just visiting the address
def delete_note(request, note_id):
    # find the note, but ONLY if it's on one of MY bookmarks.
    # someone else's note gives a 404, so they can't delete it
    note = get_object_or_404(Note, id=note_id, bookmark__user=request.user)

    note.delete()

    return redirect("/saved/")

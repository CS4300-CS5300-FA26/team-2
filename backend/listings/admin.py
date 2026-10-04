from django.contrib import admin
from .models import Listing, Bookmark

# lets us add and see listings on the /admin/ page
admin.site.register(Listing)

# lets us see and manage saved jobs on the /admin/ page
admin.site.register(Bookmark)

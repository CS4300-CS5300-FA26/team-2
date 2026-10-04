from django.contrib import admin

from .models import Listing

# lets us add and see listings on the /admin/ page
admin.site.register(Listing)

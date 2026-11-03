from django.contrib import admin

from .models import Alert, Notification

admin.site.register(Alert)
admin.site.register(Notification)

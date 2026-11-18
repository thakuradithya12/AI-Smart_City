from django.contrib import admin

from .models import Complaint, ComplaintMessage, Evidence, Resolution, StatusEvent

admin.site.register((Complaint, ComplaintMessage, Evidence, Resolution, StatusEvent))

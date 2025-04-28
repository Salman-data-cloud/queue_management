from django.contrib import admin
from .models import User, Appointment, Feedback

admin.site.register(User)
admin.site.register(Appointment)
admin.site.register(Feedback)

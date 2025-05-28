from django.contrib import admin
from unfold.admin import ModelAdmin

from django.contrib.auth import get_user_model
from .models import StudentProfile, Notification, NotificationRecipient

User = get_user_model() 

@admin.register(User)
@admin.register(StudentProfile)
@admin.register(Notification)
@admin.register(NotificationRecipient)
class CustomAdminClass(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
   
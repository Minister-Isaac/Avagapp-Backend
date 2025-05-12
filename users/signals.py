# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import StudentProfile
from .choices import UserType

User = get_user_model()

@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.role == UserType.STUDENT:
        StudentProfile.objects.create(student=instance)

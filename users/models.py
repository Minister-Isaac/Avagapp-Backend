from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from avag_learning.models.models import BaseModel

from users.choices import UserType


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have a is_superuser=True")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin, BaseModel):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=50, choices=UserType.choices)
    institution = models.ForeignKey("learning.Institution", null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # New fields for Teacher information
    subject_taught = models.ForeignKey("learning.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS =["first_name"]
    
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"

 
class StudentProfile(BaseModel):
    student = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    points = models.IntegerField(default=0)
    medals = models.IntegerField(default=0)
    activities_completed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.student.first_name}'s Profile"
    

class NotificationRecipient(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'notification')


class Notification(BaseModel):
    title = models.CharField(max_length=255, help_text="The title of the notification.", blank=True)
    recipients = models.ManyToManyField(
        CustomUser,
        through='NotificationRecipient',
        related_name='notifications',
        help_text="Select one or more users to receive this notification."
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text="The admin or teacher who created this notification (optional)."
    )
    message = models.TextField(
        help_text="The main content or details of the notification."
    )

    def __str__(self):
        return f"Message: {self.message}"
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
)

from users.choices import UserType


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        user.save()
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have a is_superuser=True")
        return self.create_user(email, full_name, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=50, choices=UserType.choices)
    institution = models.ForeignKey("learning.Institution", null=True, blank=True, on_delete=models.SET_NULL)
    
    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS =["username"]
    
    def __str__(self) -> str:
        return self.username
    
    
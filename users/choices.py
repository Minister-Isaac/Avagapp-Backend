from django.db import models


class UserType(models.TextChoices):
    STUDENT = ("student", "Student")
    TEACHER = ("teacher", "Teacher")
    ADMIN = ("admin", "Admin")

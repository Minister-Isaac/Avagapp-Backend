from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, TeacherViewSet, UserViewSet
    )

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"notifications", NotificationViewSet, basename="notification")



urlpatterns = [
    
    path("", include(router.urls)),
]
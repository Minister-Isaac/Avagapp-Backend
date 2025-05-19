from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, StudentProfileViewSet, TeacherViewSet,
    UserViewSet
    )

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r'student-profile', StudentProfileViewSet, basename='student-profile')




urlpatterns = [
    
    path("", include(router.urls)),
]
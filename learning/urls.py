from django.urls import path
from .views import LandingPageAPIView

urlpatterns = [
    path("dashboard/", LandingPageAPIView.as_view(), name="student-dashboard"),
]

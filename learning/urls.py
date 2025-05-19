from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentDashboardAPIView, KnowledgeTrailViewSet,
    LeaderboardViewSet, StudentActivityAPIView, QuestionViewSet,
    OptionalViewSet,GameViewSet, StudentAnswerViewSet, SubjectViestSet
    )


router = DefaultRouter()
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"options", OptionalViewSet, basename="options")
router.register(r"knowledge-trail", KnowledgeTrailViewSet, basename="knowledge-trail")
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')
router.register(r"games", GameViewSet, basename="games")
router.register(r"student-answers", StudentAnswerViewSet, basename="student-answers")
router.register(r"subjects", SubjectViestSet, basename="subjects")


urlpatterns = [
    path("dashboard/", StudentDashboardAPIView.as_view(), name="student-dashboard"),
    path("student-activity/", StudentActivityAPIView.as_view(), name="student-activity"),
    path("", include(router.urls)),
]

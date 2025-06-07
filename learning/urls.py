from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CertificateViewSet, StatisticsViewSet, StudentDashboardAPIView,
    KnowledgeTrailViewSet, LeaderboardViewSet, StudentActivityAPIView,
    QuestionViewSet, OptionalViewSet, GameViewSet,
    StudentAnswerViewSet, SubjectViestSet, PlayedGameViewSet, ModuleViewSet
)


router = DefaultRouter()
router.register(r"questions", QuestionViewSet, basename="question")
router.register(r"options", OptionalViewSet, basename="option")
router.register(r"knowledge-trail", KnowledgeTrailViewSet, basename="knowledge-trail")
router.register(r"leaderboard", LeaderboardViewSet, basename="leaderboard")
router.register(r"games", GameViewSet, basename="game")
router.register(r"student-answers", StudentAnswerViewSet, basename="student-answer")
router.register(r"subjects", SubjectViestSet, basename="subject")
router.register(r"statistics", StatisticsViewSet, basename="statistic")
router.register(r"certificates", CertificateViewSet, basename="certificate")
router.register(r"playedgame", PlayedGameViewSet, basename="playedgame")
router.register(r"modules", ModuleViewSet, basename="module")

urlpatterns = [
    path("dashboard/", StudentDashboardAPIView.as_view(), name="student-dashboard"),
    path("student-activity/", StudentActivityAPIView.as_view(), name="student-activity"),
    path("", include(router.urls)),
]

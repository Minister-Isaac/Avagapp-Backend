from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import KnowledgeTrail, LeaderboardEntry, Achievement
from users.models import StudentProfile
from .serializers import (
    KnowledgeTrailSerializer,LeaderboardEntrySerializer,
    AchievementSerializer
)
from users.serializers import UserSerializer, StudentProfileSerializer


class LandingPageAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    

    def get(self, request):
        user = request.user
        profile = StudentProfile.objects.get(student=user)
        achievements = Achievement.objects.filter(student=user)
        knowledge_trail = KnowledgeTrail.objects.filter(student=user).order_by("module__order")[:4]
        leaderboard = LeaderboardEntry.objects.all()[:3]  # Top 3

        return Response({
            "user": UserSerializer(user).data,
            "profile": StudentProfileSerializer(profile).data,
            "achievements": AchievementSerializer(achievements, many=True).data,
            "knowledge_trail": KnowledgeTrailSerializer(knowledge_trail, many=True).data,
            "leaderboard": LeaderboardEntrySerializer(leaderboard, many=True).data
        })

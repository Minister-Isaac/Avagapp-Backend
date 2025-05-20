from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from users.choices import UserType

from .models import (
    Game, KnowledgeTrail, Achievement, Option, Statistics, StudentAnswer,
    Subject, Question, PlayedGame
    )
from .serializers import (
    DashboardSerializer, GameSerializer, KnowledgeTrailSerializer,
    AchievementSerializer, OptionSerializer,
    PlayedGameSerializer, QuestionSerializer, StudentAnswerSerializer,
    SubjectSerializer,
    StudentLeaderboardSerializer
)
from users.models import StudentProfile
from users.serializers import UserSerializer, StudentProfileSerializer


User = get_user_model()

class SubjectViestSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class OptionalViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


class GameViewSet(viewsets.ModelViewSet):  
    serializer_class = GameSerializer
    queryset = Game.objects.all().order_by("id")
    

class StudentDashboardAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        student_profile = get_object_or_404(StudentProfile, student=user)

        # Fetch user details
        user_data = UserSerializer(user).data

        # Fetch student profile details (now includes rank, total score, etc.)
        profile_data = DashboardSerializer(student_profile).data

        # Fetch recent achievements
        achievements = Achievement.objects.filter(student=user).order_by('-awarded_at')[:4]
        achievements_data = AchievementSerializer(achievements, many=True).data

        # Fetch recent knowledge trail items
        knowledge_trail = KnowledgeTrail.objects.filter(assigned_by=user).order_by('?')[:3]
        knowledge_trail_data = KnowledgeTrailSerializer(knowledge_trail, many=True).data

        # Calculate top 3 for classification (we'll fetch the top 3 profiles and serialize them)
        top_profiles = StudentProfile.objects.annotate(
            total_score=Sum('student__playedgame__score')
        ).order_by('-total_score')[:3]

        leaderboard_data = []
        rank = 1
        for profile in top_profiles:
            leaderboard_entry = DashboardSerializer(profile).data
            leaderboard_entry['rank'] = rank
            leaderboard_data.append(leaderboard_entry)
            rank += 1

        return Response({
            "user": user_data,
            "points": profile_data.get('points', 0),
            "medal": profile_data.get('medals', 0),
            "level": profile_data.get('level', 1),
            "activities": profile_data.get('activities_completed', 0),
            "achievements": achievements_data,
            "knowledge_trail": knowledge_trail_data,
            "classification": leaderboard_data,
        })


class KnowledgeTrailViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeTrail.objects.all().order_by('-created_at')
    serializer_class = KnowledgeTrailSerializer

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)
        
    def get_queryset(self):
        user = self.request.user
        if user.role == UserType.TEACHER:
            # Teachers can only see the knowledge trails they created
            return KnowledgeTrail.objects.filter(assigned_by=user).order_by("id")
        else:
            return KnowledgeTrail.objects.all().order_by("id")

    @action(detail=False, methods=["GET"], url_path="activity")
    def get_watched_video(self, request):
        knowledge_trails = KnowledgeTrail.objects.filter(is_watched=True).order_by("id")[:4]
        serializer = KnowledgeTrailSerializer(knowledge_trails, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class StudentActivityAPIView(APIView):

    def get(self, request):
        user = request.user

        played_games = Game.objects.filter(played_game=True).order_by("id")[:4]
        knowledge_trails_watched_video = KnowledgeTrail.objects.filter(is_watched=True).order_by("id")[:4]
        knowledge_trails_pdf = KnowledgeTrail.objects.filter(pdf_file__isnull=False).order_by("id")[:4]
        
        return Response({
            "played_games": GameSerializer(played_games, many=True).data,
            "knowledge_trails_watched_video": KnowledgeTrailSerializer(knowledge_trails_watched_video, many=True).data,
            "knowledge_trails_pdf": KnowledgeTrailSerializer(knowledge_trails_pdf, many=True).data,
        }, status=status.HTTP_200_OK)


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentLeaderboardSerializer
    queryset = StudentProfile.objects.select_related('student')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(total_score=Sum('student__playedgame__score')).order_by('-total_score')

        limit = request.query_params.get('limit', 50)
        page = request.query_params.get('page', 1)

        paginator = Paginator(queryset, limit)
        try:
            leaderboard_page = paginator.page(page)
        except PageNotAnInteger:
            leaderboard_page = paginator.page(1)
        except EmptyPage:
            leaderboard_page = Paginator([], limit).page(1)

        serializer = self.get_serializer(leaderboard_page, many=True)
        ranked_data = []
        base_rank = (int(page) - 1) * int(limit)
        for i, item in enumerate(serializer.data):
            item['rank'] = base_rank + i + 1
            ranked_data.append(item)

        return Response({
            'totalCount': paginator.count,
            'totalPages': paginator.num_pages,
            'currentPage': leaderboard_page.number,
            'leaderboard': ranked_data
        })


class StudentAnswerViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswer.objects.all()
    serializer_class = StudentAnswerSerializer

    def perform_create(self, serializer):
        # Automatically associate the logged-in student with the answer
        serializer.save(student=self.request.user)


class StatisticsViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["GET"], url_path="counts")
    def get_counts(self, request):
        # Get the current counts
        current_student_count = User.objects.filter(role=UserType.STUDENT).count()
        current_teacher_count = User.objects.filter(role=UserType.TEACHER).count()
        current_video_count = KnowledgeTrail.objects.filter(video_file__isnull=False).count()
        current_pdf_count = KnowledgeTrail.objects.filter(pdf_file__isnull=False).count()

        # Get or create the statistics record
        stats, created = Statistics.objects.get_or_create(id=1)

        # Calculate the differences
        student_diff = current_student_count - stats.students
        teacher_diff = current_teacher_count - stats.teachers
        video_diff = current_video_count - stats.knowledge_trail_videos
        pdf_diff = current_pdf_count - stats.knowledge_trail_pdfs

        # Update the statistics record
        stats.students = current_student_count
        stats.teachers = current_teacher_count
        stats.knowledge_trail_videos = current_video_count
        stats.knowledge_trail_pdfs = current_pdf_count
        stats.save()

        # Return the counts and differences in the response
        return Response({
            "students": {
                "count": current_student_count,
                "difference": student_diff
            },
            "teachers": {
                "count": current_teacher_count,
                "difference": teacher_diff
            },
            "knowledge_trail_videos": {
                "count": current_video_count,
                "difference": video_diff
            },
            "knowledge_trail_pdfs": {
                "count": current_pdf_count,
                "difference": pdf_diff
            }
        }, status=status.HTTP_200_OK)
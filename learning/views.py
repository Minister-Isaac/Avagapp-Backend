from datetime import datetime
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.lib.utils import ImageReader
from django.conf import settings
import os

from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum, Max

from users.choices import UserType

from .models import (
    Game, KnowledgeTrail, Achievement, Option, Statistics, StudentAnswer,
    Subject, Question, PlayedGame, Certificate
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


# class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
#     serializer_class = StudentLeaderboardSerializer
#     queryset = StudentProfile.objects.select_related('student')

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset().annotate(total_score=Sum('student__playedgame__score')).order_by('-total_score')

#         limit = request.query_params.get('limit', 50)
#         page = request.query_params.get('page', 1)

#         paginator = Paginator(queryset, limit)
#         try:
#             leaderboard_page = paginator.page(page)
#         except PageNotAnInteger:
#             leaderboard_page = paginator.page(1)
#         except EmptyPage:
#             leaderboard_page = Paginator([], limit).page(1)

#         serializer = self.get_serializer(leaderboard_page, many=True)
#         ranked_data = []
#         base_rank = (int(page) - 1) * int(limit)
#         for i, item in enumerate(serializer.data):
#             item['rank'] = base_rank + i + 1
#             ranked_data.append(item)

#         return Response({
#             'totalCount': paginator.count,
#             'totalPages': paginator.num_pages,
#             'currentPage': leaderboard_page.number,
#             'leaderboard': ranked_data
#         })


class LeaderboardViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["GET"], url_path="leaderboard")
    def leaderboard(self, request):
        # Aggregate total scores and last activity for each student
        leaderboard_data = (
            PlayedGame.objects.values("student__id", "student__first_name", "student__last_name", "student__avatar")
            .annotate(
                total_score=Sum("score"),
                last_activity=Max("played_at")
            )
            .order_by("-total_score")  # Order by total score in descending order
        )

        # Format the response
        leaderboard = [
            {   
                "image": entry["student__avatar"] if entry["student__avatar"] else None,
                "student_name": f"{entry['student__first_name']} {entry['student__last_name']}",
                "score": entry["total_score"],
                "last_activity": entry["last_activity"]
            }
            for entry in leaderboard_data
        ]

        return Response(leaderboard, status=200)
    

class StudentAnswerViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswer.objects.all()
    serializer_class = StudentAnswerSerializer

    def perform_create(self, serializer):
        # Automatically associate the logged-in student with the answer
        serializer.save(student=self.request.user)


class StatisticsViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["GET"], url_path="admin-stats")
    def get_admin_stats(self, request):
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
    
    @action(detail=False, methods=["GET"], url_path="teacher-stats")
    def get_teacher_stats(self, request):
        
        # Get the current counts
        current_student_count = User.objects.filter(role=UserType.STUDENT).count()
        current_teacher_count = User.objects.filter(role=UserType.TEACHER).count()
        current_video_count = KnowledgeTrail.objects.filter(video_file__isnull=False).count()
        current_certificate_count = Certificate.objects.filter(student__isnull=False).count()

        # Get or create the statistics record
        stats, created = Statistics.objects.get_or_create(id=1)

        new_certificates = Certificate.objects.filter(created_at__gt=stats.last_updated).count()
        
        # Calculate the differences
        student_diff = current_student_count - stats.students
        teacher_diff = current_teacher_count - stats.teachers
        video_diff = current_video_count - stats.knowledge_trail_videos

        # Update the statistics record
        stats.students = current_student_count
        stats.teachers = current_teacher_count
        stats.knowledge_trail_videos = current_video_count
        stats.certificates_issued += new_certificates
        stats.last_updated = datetime.now()
        stats.save()

        # Return the counts and differences in the response
        return Response({
            "students": {
                "count": current_student_count,
                "difference": student_diff
            },
            "classes": {
                "count": current_teacher_count,
                "difference": teacher_diff
            },
            "lessons": {
                "count": current_video_count,
                "difference": video_diff
            },
            "Certificates": {
                "count": current_certificate_count,
                "new_certificates": new_certificates
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["GET"], url_path="student-stats")
    def get_student_stats(self, request):
        student = request.user
        # Get the student's profile
        student_profile = StudentProfile.objects.get(student=student)

        # Get the current counts
        current_student_point_count = student_profile.points
        current_student_medals_count = student_profile.medals
        played_games_count = PlayedGame.objects.filter(student=student).count()
        current_certificate_count = Certificate.objects.filter(student=student).count()

        # Get or create the statistics record
        stats, created = Statistics.objects.get_or_create(id=1)

        new_certificates = Certificate.objects.filter(student=student, created_at__gt=stats.last_updated).count()
        new_played_games = PlayedGame.objects.filter(student=student, played_at__gt=stats.last_updated).count()
        
        # Calculate the differences
        student_point_diff = current_student_point_count - stats.student_points
        student_medals_diff = current_student_medals_count - stats.student_medals
        
        # Update the statistics record
        stats.student_points = student_point_diff
        stats.student_medals = student_medals_diff
        stats.certificates_issued += new_certificates
        stats.last_updated = datetime.now()
        stats.save()

        # Return the counts and differences in the response
        return Response({
            "points": {
                "count": current_student_point_count,
                "difference": student_point_diff
            },
            "medals": {
                "count": current_student_medals_count,
                "difference": student_medals_diff
            },
            "played_games": {
                    "count": played_games_count,
                    "new_played_games": new_played_games
            },
            "certificates": {
                "count": current_certificate_count,
                "new_certificates": new_certificates
            }
        }, status=status.HTTP_200_OK)
   

class CertificateViewSet(viewsets.ViewSet):
    @action(detail=True, methods=["POST"], url_path="generate-certificate")
    def generate_certificate(self, request, pk=None):
        # Ensure the requesting user is a teacher
        if request.user.role != UserType.TEACHER:
            return Response({"error": "Only teachers can generate certificates."}, status=status.HTTP_403_FORBIDDEN)

        # Get the student
        try:
            student = User.objects.get(pk=pk, role=UserType.STUDENT)
        except User.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        return self._generate_certificate_for_student(student, request)
    
    @action(detail=False, methods=["POST"], url_path="generate-certificates-for-all")
    def generate_certificates_for_all(self, request):
        # Ensure the requesting user is a teacher
        if request.user.role != UserType.TEACHER:
            return Response({"error": "Only teachers can generate certificates."}, status=status.HTTP_403_FORBIDDEN)

        # Get all students
        students = User.objects.filter(role=UserType.STUDENT)

        # List to store certificate URLs
        certificate_urls = []
        
        # Generate certificates for each student
        for student in students:
            response = self._generate_certificate_for_student(student, request)
            if response.status_code == status.HTTP_201_CREATED:
                certificate_urls.append({
                    "student": f"{student.first_name} {student.last_name}",
                    "certificate_url": response.data.get("certificate_url")
                })

        return Response({
            "message": "Certificates generated successfully for all students.",
            "certificates": certificate_urls
            }, 
            status=status.HTTP_201_CREATED)
    
    def _generate_certificate_for_student(self, student, request):
        # Generate the PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Add a subtle border
        pdf.setStrokeColor(colors.grey)
        pdf.setLineWidth(1)
        pdf.rect(40, 40, width - 80, height - 80)

        # === LOGO ===
        logo_path = os.path.join(settings.BASE_DIR, "static/certificates/logo.png")
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            pdf.drawImage(logo, width/2 - 75, height - 100, width=150, height=60, mask='auto')

        # Add the issuance date (top left, similar to Coursera)
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.black)
        issuance_date = datetime.now().strftime('%B %d, %Y')
        pdf.drawString(50, height - 90, issuance_date)

        # Add the student's name (large, centered)
        pdf.setFont("Helvetica-Bold", 24)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, height - 160, f"{student.first_name} {student.last_name}")

        # Add the completion message
        pdf.setFont("Helvetica", 14)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, height - 200, "has successfully completed")

        # Add the course/game title (example: "Knowledge Trail")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.setFillColor(colors.darkblue)
        pdf.drawCentredString(width / 2, height - 240, "Knowledge Trail")

        # Add course description (similar to Coursera's "an online non-credit course...")
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, height - 270, "an online gamified learning module authorized by AVAG")

        # Add issuer information (bottom)
        pdf.setFont("Helvetica", 12)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(width / 2, 100, f"Issued by: {request.user.first_name}")

        # Add branding (bottom right, similar to Coursera's "Meta" and "Coursera")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.darkblue)
        pdf.drawString(width - 200, 60, "AVAG Learning Platform")

        # Save the PDF
        pdf.save()

        # Save the PDF to the Certificate model
        buffer.seek(0)
        pdf_file = ContentFile(buffer.read(), f"certificate_{student.first_name}.pdf")
        certificate = Certificate.objects.create(student=student, file=pdf_file)
        buffer.close()
        
        return Response({"message": f"Certificate generated successfully. for {student.first_name} {student.last_name}", "certificate_url": certificate.file.url}, status=status.HTTP_201_CREATED)
    
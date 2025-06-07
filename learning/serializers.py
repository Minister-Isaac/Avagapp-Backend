from rest_framework import serializers

from learning.choices import QuestionType
from users.choices import UserType
from users.models import StudentProfile
from .models import (
    Achievement,
    Badge,
    Game,
    Institution,
    PlayedGame,
    Question,
    Option,
    StudentAnswer,
    Certificate,
    KnowledgeTrail,
    Subject,
    Topic,
    UserAttendance,
    Module
)

from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"
        

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = "__all__"
        


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "option_text", "is_correct", "order"]

     
class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)
    class Meta:
        model = Question
        fields = ["id", "question_text", "question_type", "points", "options", "correct_answer"]


class GameSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Game
        fields = ["id", "title", "badges_awarded", "questions"]

    def create(self, validated_data):
        user = self.context.get("request").user
        roles = [UserType.ADMIN, UserType.TEACHER]
        if user.role not in roles:
            raise serializers.ValidationError("Only teachers or admins can create games.")

        questions_data = validated_data.pop("questions")
        game = Game.objects.create(**validated_data)

        for question_data in questions_data:
            qtype = question_data.get("question_type")
            correct_answer = question_data.pop("correct_answer", None)

            if qtype == QuestionType.FILL_IN_THE_BLANK:
                if not correct_answer:
                    raise serializers.ValidationError(
                        "This field is required for fill-in-the-blank questions."
                    )
                options_data = []
            else:
                options_data = question_data.pop("options", [])

            question = Question.objects.create(**question_data, correct_answer=correct_answer)
            for option_data in options_data:
                Option.objects.create(question=question, **option_data)

            question.games.add(game)
        return game


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = "__all__"


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"


# class KnowledgeTrailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = KnowledgeTrail
#         fields = "__all__"


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "description", "image"]


class AchievementSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()

    class Meta:
        model = Achievement
        fields = ["badge", "awarded_at"]


class KnowledgeTrailSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    assigned_by_name = serializers.CharField(source="assigned_by.first_name", read_only=True)
    media_url = serializers.SerializerMethodField()
    target_students = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role=UserType.STUDENT),
        required=False
    )

    class Meta:
        model = KnowledgeTrail
        fields = [
            "id",
            "title",
            "subject",
            "subject_name",
            "assigned_by_name",
            "media_url",
            "pdf_file",
            "video_file",
            "thumbnail",
            "description",
            "recommended",
            "is_watched",
            "is_public",
            "target_students",
        ]

    def validate(self, data):
        pdf_file = data.get("pdf_file")
        video_file = data.get("video_file")
        
        if pdf_file and video_file:
            raise serializers.ValidationError("You can either upload video or pdf file.")
        if pdf_file:
            if not self.is_pdf(pdf_file):
                raise serializers.ValidationError("Only PDF files are allowed.")
        if video_file:
            if not self.is_video(video_file):
                raise serializers.ValidationError("Only video files are allowed (mp4, avi, mov, mkv, webm).")
        return data
    
    def is_pdf(self, value):
        return value.name.lower().endswith('.pdf')

    def is_video(self, value):
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        return value.name.lower().endswith(tuple(video_extensions))

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        elif obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def create(self, validated_data):
        request = self.context.get("request")
        roles = [UserType.ADMIN, UserType.TEACHER]
        if request.user.role not in roles:
            raise serializers.ValidationError("Only teachers or admin can create KnowledgeTrail.")
        
        target_students = validated_data.pop("target_students", [])
        is_public = validated_data.get("is_public", True)
        
        if not is_public and not target_students:
            raise serializers.ValidationError("When creating a private KnowledgeTrail, you must select at least one student.")
        
        # Assign the current user as the 'assigned_by' field
        validated_data["assigned_by"] = request.user
        
        # Create the KnowledgeTrail instance
        knowledge_trail = super().create(validated_data)
        
        # Add target students if any
        if target_students:
            knowledge_trail.target_students.set(target_students)
        
        return knowledge_trail


class PlayedGameSerializer(serializers.ModelSerializer):
    game = GameSerializer()

    class Meta:
        model = PlayedGame
        fields = ["id", "game", "score", "duration", "completed", "played_at"]
        read_only_fields = ['played_at']


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(read_only=True)
    studentId = serializers.IntegerField(source='student.id', read_only=True)
    name = serializers.CharField(source='student.first_name', read_only=True)
    profileImageUrl = serializers.SerializerMethodField()
    score = serializers.IntegerField(read_only=True)
    level = serializers.SerializerMethodField()
    attendance = serializers.SerializerMethodField()
    lastActivity = serializers.DateTimeField(source='played_at', read_only=True)

    class Meta:
        model = PlayedGame
        fields = ['rank', 'studentId', 'name', 'profileImageUrl', 'score', 'level', 'attendance', 'lastActivity']

    def get_profileImageUrl(self, obj):
        try:
            return obj.student.avatar.url if obj.student.avatar else "/static/images/default_avatar.png" # Adjust path as needed
        except AttributeError:
            return "/static/images/default_avatar.png"

    def get_level(self, obj):
        try:
            return obj.student.profile.level
        except StudentProfile.DoesNotExist:
            return 1 # Default level

    def get_attendance(self, obj):
        
        # TODO You might need to calculate attendance based on UserAttendance model
        # For simplicity, let's return the latest attendance status if available
        try:
            latest_attendance = obj.student.userattendance_set.latest('date')
            # You can define logic here to represent attendance (e.g., boolean, percentage)
            return "Present" if latest_attendance.logout_time is None else "Present"
        except UserAttendance.DoesNotExist:
            return "N/A"

class StudentLeaderboardSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(read_only=True)
    studentId = serializers.IntegerField(source='student.id', read_only=True)
    name = serializers.CharField(source='student.first_name', read_only=True)
    profileImageUrl = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    attendance = serializers.SerializerMethodField()
    lastActivity = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = ['rank', 'studentId', 'name', 'profileImageUrl', 'score', 'attendance', 'lastActivity']

    def get_profileImageUrl(self, obj):
        return obj.student.avatar.url if obj.student.avatar else "/static/images/default_avatar.png" # Adjust path as needed

    def get_score(self, obj):
        # Calculate total score for the student across all played games
        total_score = obj.student.playedgame_set.aggregate(total=Sum('score'))['total'] or 0
        return total_score

    def get_attendance(self, obj):
        # Calculate attendance based on UserAttendance (e.g., percentage of present days)
        today = timezone.now().date()
        start_date = today - timedelta(days=30) # Consider last 30 days
        present_days = obj.student.userattendance_set.filter(login_time__date__gte=start_date).count()
        total_days = (today - start_date).days + 1
        if total_days > 0:
            return f"{round((present_days / total_days) * 100)}%"
        return "N/A"

    def get_lastActivity(self, obj):
        # Get the last time the student interacted with a game
        last_played = obj.student.playedgame_set.order_by('-played_at').first()
        return last_played.played_at if last_played else None


class DashboardSerializer(serializers.ModelSerializer):
    leaderboard_rank = serializers.SerializerMethodField()
    total_score = serializers.SerializerMethodField()
    attendance = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = ['points', 'medals', 'level', 'activities_completed', 'leaderboard_rank', 'total_score', 'attendance', 'last_activity']

    def get_leaderboard_rank(self, obj):
        # Calculate rank based on total score
        queryset = StudentProfile.objects.annotate(
            total_score=Sum('student__playedgame__score')
        ).order_by('-total_score')
        rank = 1
        for profile in queryset:
            if profile.id == obj.id:
                return rank
            rank += 1
        return None

    def get_total_score(self, obj):
        total_score = obj.student.playedgame_set.aggregate(total=Sum('score'))['total'] or 0
        return total_score

    def get_attendance(self, obj):
        # Calculate attendance based on UserAttendance (example: percentage of present days)
        today = timezone.now().date()
        start_date = today - timedelta(days=30) # Consider last 30 days
        present_days = obj.student.userattendance_set.filter(login_time__date__gte=start_date).count()
        total_days = (today - start_date).days + 1
        if total_days > 0:
            return f"{round((present_days / total_days) * 100)}%"
        return "N/A"

    def get_last_activity(self, obj):
        # Get the last time the student interacted with a game
        last_played = obj.student.playedgame_set.order_by('-played_at').first()
        return last_played.played_at if last_played else None
    

class StudentForCertificateSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profileImageUrl = serializers.SerializerMethodField()
    medals = serializers.IntegerField(source='profile.medals', read_only=True)
    score = serializers.SerializerMethodField()  # You'll need to define how to get the relevant score
    performance = serializers.SerializerMethodField()  # You'll need to define how to calculate performance

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profileImageUrl', 'medals', 'score', 'performance']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_score(self, obj):
        # TODO Implement logic to get the relevant score for certificate generation
        # This might be total points, score in a specific course, etc.
        return obj.profile.points  

    def get_performance(self, obj):
        # TODO Implement logic to calculate performance (e.g., based on completed activities, quiz scores)
        return 0.90  # Placeholder


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = "__all__"

    def create(self, validated_data):
        # Create the StudentAnswer instance
        student_answer = StudentAnswer.objects.create(**validated_data)

        # The `save` method in the model will handle updating the student's points
        return student_answer


class ModuleSerializer(serializers.ModelSerializer):
    knowledge_trails = KnowledgeTrailSerializer(many=True, read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.first_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'subject', 'subject_name',
            'order', 'assigned_by_name', 'knowledge_trails'
        ]

    def create(self, validated_data):
        user = self.context.get('request').user
        roles = [UserType.ADMIN, UserType.TEACHER]
        if user.role not in roles:
            raise serializers.ValidationError("Only teachers or admins can create modules.")
        validated_data['assigned_by'] = user
        return super().create(validated_data)

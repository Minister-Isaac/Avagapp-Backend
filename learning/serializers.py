from rest_framework import serializers
from .models import (
    Achievement,
    Badge,
    Institution,
    Course,
    LeaderboardEntry,
    Module,
    Question,
    Quiz,
    Option,
    StudentAnswer,
    Certificate,
    KnowledgeTrail,
    Subject,
    Topic
)

from users.serializers import UserSerializer


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
        

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = "__all__"
     
   
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"

      
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = "__all__"


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = "__all__"


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"


class KnowledgeTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeTrail
        fields = "__all__"


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["name", "description", "image"]


class AchievementSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()

    class Meta:
        model = Achievement
        fields = ["badge", "awarded_at"]


class KnowledgeTrailSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source="module.title")
    course_title = serializers.CharField(source="module.course.title")

    class Meta:
        model = KnowledgeTrail
        fields = ["module_title", "course_title", "is_complete"]

class LeaderboardEntrySerializer(serializers.ModelSerializer):
    student = UserSerializer()

    class Meta:
        model = LeaderboardEntry
        fields = ["student", "score", "rank", "level"]
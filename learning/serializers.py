from rest_framework.serializers import ModelSerializer
from .models import (
    Institution,
    Course,
    Module,
    Question,
    Quiz,
    Option,
    StudentAnswer,
    Certificate,
    KnowledgeTrail
)


class InstitutionSerializer(ModelSerializer):
    class Meta:
        model = Institution
        fields = "__all__"
        

class ModuleSerializer(ModelSerializer):
    class Meta:
        model = Module
        fields = "__all__"
     
   
class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"

      
class QuestionSerializer(ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        

class QuizSerializer(ModelSerializer):
    class Meta:
        model = Quiz
        fields = "__all__"


class OptionSerializer(ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"


class StudentAnswerSerializer(ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = "__all__"


class CertificateSerializer(ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"


class KnowledgeTrailSerializer(ModelSerializer):
    class Meta:
        model = KnowledgeTrail
        fields = "__all__"

from django.db import models
from django.contrib.auth import get_user_model

from avag_learning.models.models import BaseModel
from learning.choices import  MediaType, QuestionType
from users.models import StudentProfile

User = get_user_model()

class Subject(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    
class Topic(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    
    
class Institution(BaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
 

class Question(BaseModel):
    question_text = models.TextField(help_text="The main text of the question.")
    question_type = models.CharField(
        max_length=50,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
        help_text="The type of question (e.g., multiple choice, fill in the gap)."
        )
    points = models.PositiveIntegerField(
        default=1,
        help_text="Points awarded for correctly answering this question."
        )
    

class Option(BaseModel):
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    option_text = models.CharField(
        max_length=255,
        help_text="The text of this answer option.")  # The text of the answer option
    is_correct = models.BooleanField(
        default=False,
        help_text="Whether this option is the correct answer to the question.")
    

class StudentAnswer(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    

class Certificate(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="certificate/")
    issued_at = models.DateTimeField(auto_now_add=True)
    

class KnowledgeTrail(BaseModel):
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="knowledge_items")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.VIDEO)
    media_file = models.FileField(upload_to="knowledge_media/", null=True, blank=True)
    thumbnail = models.ImageField(upload_to="knowledge_thumbnails/", null=True, blank=True)
    description = models.TextField(blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.assigned_by} - {self.title}"
    

class Badge(BaseModel):
    name = models.CharField(max_length=100)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    
    def __str__(self):
        return self.name
        
    
class Achievement(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.first_name} - {self.badge.name} - {self.awarded_at}"


class Game(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='game_thumbnails/', null=True, blank=True)
    max_score = models.IntegerField(default=100)
    reward_points = models.PositiveIntegerField(default=10)
    badges_awarded = models.CharField(max_length=255, blank=True, help_text="Comma-separated badge names if any")
    questions = models.ManyToManyField('Question', related_name='games', blank=True)

    def __str__(self):
        return self.title
    
    @property
    def reward_points(self):
        return self.questions.aggregate(total_points=models.Sum('points'))['total_points'] or 0


class PlayedGame(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    duration = models.DurationField(null=True, blank=True)  # Time spent playing
    completed = models.BooleanField(default=False)
    played_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} played {self.game} ({self.score} pts)"


class UserAttendance(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date') # Ensure only one attendance record per student per day

    def __str__(self):
        return f"{self.student.first_name} - {self.date}"
    
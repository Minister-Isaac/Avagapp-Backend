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
        default=QuestionType.QUIZ,
        help_text="The type of question (e.g., quit, fill in the blank etc)."
        )
    points = models.PositiveIntegerField(
        default=1,
        help_text="Points awarded for correctly answering this question."
        )
    correct_answer = models.TextField(
        null=True,
        blank=True,
        help_text="The correct answer for 'fill in the gap' questions."
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
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    typed_answer = models.TextField(null=True, blank=True, help_text="The student's answer for 'fill in the blank' questions.")
    
    def save(self, *args, **kwargs):
         # Check if the question is 'fill in the blank'
        if self.question.question_type == QuestionType.FILL_IN_THE_BLANK:
            # Compare the student's typed answer with the correct answer
            if self.typed_answer and self.question.correct_answer:
                # Normalize answers (case-insensitive and strip whitespace)
                if self.typed_answer.strip().lower() == self.question.correct_answer.strip().lower():
                    self._update_student_points(self.question.points)
                          
        # Check if the selected option is correct
        else:
            # For other question types, check if the selected option is correct
            if self.selected_option and self.selected_option.is_correct:
                self._update_student_points(self.question.points)
                
        super().save(*args, **kwargs)
        # Check if the game is completed and award madals
        self._check_and_award_medals()
        
    
    def _update_student_points(self, points):
        # Get or create  the student's profile
        student_profile, created = StudentProfile.objects.get_or_create(student=self.student)
        # Add the question's points to the student's points
        student_profile.points += points
        student_profile.save()
        
    def _check_and_award_medals(self):
        # Get the games associated with the question
        games = self.question.games.all()
        for game in games:
            # Get all questions in the game
            total_questions = game.questions.count()

            # Get the number of answers the student has submitted for this game
            answered_questions = StudentAnswer.objects.filter(
                student=self.student,
                question__in=game.questions.all()
            ).count()

            # Only proceed if the student has answered all questions in the game
            if answered_questions == total_questions:
                # Get the number of correct answers given by the student for this game
                correct_answers = StudentAnswer.objects.filter(
                    student=self.student,
                    question__in=game.questions.all()
                ).filter(
                    models.Q(selected_option__is_correct=True) |
                    models.Q(typed_answer__iexact=models.F('question__correct_answer'))
                ).count()

                # Calculate the percentage score
                percentage_score = (correct_answers / total_questions) * 100
                print(f"Percentage Score: {percentage_score}%")
                print(f"Game: {game.title}, Total Questions: {total_questions}, Correct Answers: {correct_answers}")

                # Check if the student has achieved a medal
                if percentage_score >= 80:
                    # Award a medal to the student
                    student_profile, created = StudentProfile.objects.get_or_create(student=self.student)
                    student_profile.medals += 1
                    student_profile.save()    


class Certificate(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="certificate/")
    issued_at = models.DateTimeField(auto_now_add=True)
    

class KnowledgeTrail(BaseModel):
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="knowledge_items")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pdf_file = models.FileField(upload_to="knowledge_pdf_media/", null=True, blank=True)
    video_file = models.FileField(upload_to="knowledge_video_media/", null=True, blank=True)
    thumbnail = models.ImageField(upload_to="knowledge_thumbnails/", null=True, blank=True)
    description = models.TextField(blank=True)
    note = models.TextField(null=True, blank=True)
    recommended = models.BooleanField(default=False)
    is_watched = models.BooleanField(default=False)

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
    reward_points = models.PositiveIntegerField(default=10)
    badges_awarded = models.CharField(max_length=255, blank=True, help_text="Comma-separated badge names if any")
    questions = models.ManyToManyField('Question', related_name='games', blank=True)
    played_game = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to="game_thumbnails/", null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    @property
    def reward_points(self):
        return self.questions.aggregate(total_points=models.Sum("points"))["total_points"] or 0


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


class Statistics(models.Model):
    students = models.IntegerField(default=0)
    teachers = models.IntegerField(default=0)
    knowledge_trail_videos = models.IntegerField(default=0)
    knowledge_trail_pdfs = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
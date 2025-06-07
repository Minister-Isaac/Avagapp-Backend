from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now

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
    order = models.PositiveIntegerField(null=True, blank=True, help_text="Correct order for matching/arranging type games.")
    

class StudentAnswer(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    typed_answer = models.TextField(null=True, blank=True, help_text="The student's answer for 'fill in the blank' questions.")
    is_correct = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_correct = False

        if self.question.question_type == QuestionType.FILL_IN_THE_BLANK:
            if self.typed_answer and self.question.correct_answer:
                is_correct = self.typed_answer.strip().lower() == self.question.correct_answer.strip().lower()

        elif self.question.question_type == QuestionType.MATCH_THE_COLUMN and self.typed_answer:
            try:
                submitted_ids = list(map(int, self.typed_answer.strip().split(',')))
                correct_ids = list(self.question.options.order_by("order").values_list("id", flat=True))
                is_correct = submitted_ids == correct_ids
            except ValueError:
                pass
        elif self.question.question_type == QuestionType.WORD_HUNT and self.typed_answer:
            try:
                # Count how many options are marked is_correct=True
                correct_count = self.question.options.filter(is_correct=True).count()
                submitted_count = int(self.typed_answer.strip())

                if submitted_count == correct_count:
                    self._update_student_points(self.question.points)
            except ValueError:
                pass  # Invalid number submitted by student

        else:
            if self.selected_option and self.selected_option.is_correct:
                is_correct = True

        if is_correct:
            self._update_student_points(self.question.points)

        self.is_correct = is_correct
        super().save(*args, **kwargs)
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
                    question__in=game.questions.all(),
                    is_correct=True
                ).count()

                # Calculate the percentage score
                percentage_score = (correct_answers / total_questions) * 100
                
                # Check if the student has achieved a medal
                if percentage_score >= 80:
                    # Award a medal to the student
                    student_profile, created = StudentProfile.objects.get_or_create(student=self.student)
                    student_profile.medals += 1
                    student_profile.save()    
                
                # Create or update the PlayedGame record
                played_game, created = PlayedGame.objects.get_or_create(
                    student=self.student,
                    game=game,
                    defaults={
                        "score": percentage_score,
                        "completed": True,
                        "played_at": now()
                    }
                )
                if not created:
                    # Update the existing PlayedGame record if it already exists
                    played_game.score = percentage_score
                    played_game.completed = True
                    played_game.played_at = now()
                    played_game.save()


class Certificate(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="certificate/")
    issued_at = models.DateTimeField(auto_now_add=True)
    

class Module(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="modules")
    order = models.PositiveIntegerField(default=0, help_text="Order in which this module appears")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.subject.name} - {self.title}"
    

class KnowledgeTrail(BaseModel):
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="knowledge_items")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="knowledge_trails", null=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Order within the module")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pdf_file = models.FileField(upload_to="knowledge_pdf_media/", null=True, blank=True)
    video_file = models.FileField(upload_to="knowledge_video_media/", null=True, blank=True)
    thumbnail = models.ImageField(upload_to="knowledge_thumbnails/", null=True, blank=True)
    description = models.TextField(blank=True)
    note = models.TextField(null=True, blank=True)
    recommended = models.BooleanField(default=False)
    is_watched = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True, help_text="If True, all students can see this. If False, only selected students can see it.")
    target_students = models.ManyToManyField(User, related_name="targeted_knowledge_trails", blank=True,
                                           help_text="Specific students who can see this knowledge trail when not public")

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
    certificates_issued = models.IntegerField(default=0)
    student_points = models.IntegerField(default=0)
    student_medals = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    last_certificate_check = models.DateTimeField(default=now)

def award_top_students_badges():
    """
    Awards Gold, Silver, and Bronze badges to the top 3 students based on their total points.
    Ensures each student only has one of these badges at a time.
    """
    
    # Get top 3 students by points
    top_students = StudentProfile.objects.order_by('-points')[:3]
    badge_names = ["Gold", "Silver", "Bronze"]
    badge_descriptions = [
        "Awarded to the student with the highest score.",
        "Awarded to the student with the second highest score.",
        "Awarded to the student with the third highest score."
    ]
    badge_images = [
        "badges/gold.png",  # You should have these images in your media folder
        "badges/silver.png",
        "badges/bronze.png"
    ]
    
    # Remove these badges from all students before re-awarding
    Badge.objects.filter(name__in=badge_names).delete()
    
    for idx, student_profile in enumerate(top_students):
        badge, _ = Badge.objects.get_or_create(
            name=badge_names[idx],
            student=student_profile.student,
            defaults={
                "description": badge_descriptions[idx],
                "image": badge_images[idx]
            }
        )
        # Optionally, create an Achievement record
        Achievement.objects.get_or_create(
            student=student_profile.student,
            badge=badge
        )
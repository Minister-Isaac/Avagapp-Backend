from django.db import models
from django.contrib.auth import get_user_model

from avag_learning.models.models import BaseModel

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
    

class Course(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    

class Module(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()


class Quiz(BaseModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    passing_score = models.IntegerField()
    

class Question(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    

class Option(BaseModel):
    question = models.ForeignKey(Question, related_name="options", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    

class StudentAnswer(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)
    

class Certificate(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    file = models.FileField(upload_to="certificate/")
    issued_at = models.DateTimeField(auto_now_add=True)
    

class KnowledgeTrail(BaseModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    is_complete = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.username} - {self.module.title} - {'Complete' if self.is_complete else 'Incomplete'}"
    

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    
    def __str__(self):
        return self.name


class LeaderboardEntry(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    level = models.PositiveIntegerField(default=0)
    attendance = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-score', 'last_activity']
        
    def __str__(self):
        return f"{self.student.username} - Rank: {self.rank}, Score: {self.score}"
    
    
class Achievement(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.badge.name} - {self.awarded_at}"
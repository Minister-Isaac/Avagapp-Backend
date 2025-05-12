from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (Badge, Certificate, Course, Institution, KnowledgeTrail,
                     LeaderboardEntry, Module, Option, Question, Quiz,
                     StudentAnswer, Subject, Topic, Achievement)
 

@admin.register(Badge)
@admin.register(Achievement)
@admin.register(Certificate)
@admin.register(Institution)
@admin.register(KnowledgeTrail)
@admin.register(LeaderboardEntry)
@admin.register(Subject)
@admin.register(Topic)
@admin.register(Course)
@admin.register(Module)
@admin.register(Quiz)
@admin.register(Question)
@admin.register(Option)
@admin.register(StudentAnswer)
class CustomAdminClass(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
   
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (Badge, Certificate, Institution, KnowledgeTrail,
                    Option, Question,PlayedGame,
                    StudentAnswer, Subject, Topic, Achievement)
 


@admin.register(PlayedGame)
@admin.register(Badge)
@admin.register(Achievement)
@admin.register(Certificate)
@admin.register(Institution)
@admin.register(KnowledgeTrail)
@admin.register(Subject)
@admin.register(Topic)
@admin.register(Question)
@admin.register(Option)
@admin.register(StudentAnswer)
class CustomAdminClass(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
   
from django.db import models
    
class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice",
    FILL_IN_THE_GAP = "fill_in_the_gap", "Fill in the Gap"
    

class MediaType(models.TextChoices):
    VIDEO = "video", "Video"
    PDF = "pdf", "PDF"
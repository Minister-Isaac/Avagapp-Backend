from django.db import models
    
class QuestionType(models.TextChoices):
    QUIZ = "quiz", "Quiz",
    FILL_IN_THE_BLANK = "fill_in_the_blank", "Fill in the blank",
    DRAG_AND_DROP = "drag_and_drop", "Drag and drop",
    MATCH_THE_COLUMN = "match_the_column", "Match the column",
    WORD_HUNT = "word_hunt", "Word hunt",
    

class MediaType(models.TextChoices):
    VIDEO = "video", "Video"
    PDF = "pdf", "PDF"
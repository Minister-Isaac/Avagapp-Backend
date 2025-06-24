from learning.models import KnowledgeTrailProgress


def has_completed_module(student, module):
    trails = module.knowledge_trails.all()
    for trail in trails:
        if not KnowledgeTrailProgress.objects.filter(student=student, knowledge_trail=trail, completed=True).exists():
            return False
    return True
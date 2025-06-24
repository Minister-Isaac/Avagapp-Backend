from django.db import migrations

def create_subjects(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    subjects = [
        "Mathematics",
        "English",
        "Biology",
        "Chemistry",
        "Physics",
        "Computer Science",
        "Economics",
        "Geography",
        "History",
        "Civic Education",
    ]
    for subject_name in subjects:
        Subject.objects.get_or_create(name=subject_name)

def delete_subjects(apps, schema_editor):
    Subject = apps.get_model("learning", "Subject")
    subject_names = [
        "Mathematics",
        "English",
        "Biology",
        "Chemistry",
        "Physics",
        "Computer Science",
        "Economics",
        "Geography",
        "History",
        "Civic Education",
    ]
    Subject.objects.filter(name__in=subject_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("learning", "0013_game_module_knowledgetrailprogress"), 
    ]
    operations = [
        migrations.RunPython(create_subjects, reverse_code=delete_subjects),
    ]

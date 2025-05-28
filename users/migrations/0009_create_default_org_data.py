from django.db import migrations, models
from django.contrib.auth import get_user_model
from users.choices import UserType

User = get_user_model()

def create_default_org_data(apps, schema_editor):
    Institution = apps.get_model("learning", "Institution")
    Subject = apps.get_model("learning", "Subject")
    
    Institution.objects.get_or_create(
        name="AVAG-E-Learning Institution"
    )
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(
            first_name="admin",
            email="avag-admin@gmail.com",
            password="avag-admin@gmail.com",
            role=UserType.ADMIN,
            )
    english, created = Subject.objects.get_or_create(name="English")

def remove_default_org_data(apps, schema_editor):
    Institution = apps.get_model("learning", "Institution")
    Subject = apps.get_model("learning", "Subject")
    User = get_user_model()

    User.objects.get(email="avag-admin@gmail.com").delete()
    Institution.objects.get(name="AVAG-E-Learning Institution").delete()
    Subject.objects.get(name="English").delete()
    
class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_studentprofile_created_at_studentprofile_updated_at"),
    ]

    operations = [
        migrations.RunPython(
            create_default_org_data,
            remove_default_org_data,
        )
    ]




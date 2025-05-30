# Generated by Django 5.1.3 on 2025-05-24 16:11

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0010_statistics'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='certificates_issued',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='statistics',
            name='last_certificate_check',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='statistics',
            name='student_medals',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='statistics',
            name='student_points',
            field=models.IntegerField(default=0),
        ),
    ]

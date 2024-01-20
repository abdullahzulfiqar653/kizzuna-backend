# Generated by Django 4.2.3 on 2024-01-20 01:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_project_summary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('id', 'Indonesian'), ('ja', 'Japanese'), ('es', 'Spanish'), ('it', 'Italian'), ('pt', 'Portuguese'), ('de', 'German'), ('pl', 'Polish'), ('fr', 'French'), ('nl', 'Dutch'), ('sv', 'Swedish')], default='en', max_length=2),
        ),
    ]

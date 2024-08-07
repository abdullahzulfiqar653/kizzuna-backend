# Generated by Django 4.2.3 on 2024-06-20 09:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0011_taskresult_periodic_task_name'),
        ('api', '0039_alter_notequestion_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='task',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_results.taskresult'),
        ),
    ]
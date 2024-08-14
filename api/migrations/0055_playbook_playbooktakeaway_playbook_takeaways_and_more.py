# Generated by Django 4.2.3 on 2024-08-14 18:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import shortuuid.django_fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0054_remove_note_is_analyzing_note_task'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayBook',
            fields=[
                ('id', shortuuid.django_fields.ShortUUIDField(alphabet=None, editable=False, length=12, max_length=12, prefix='', primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('clip', models.FileField(max_length=255, null=True, upload_to='attachments/')),
                ('thumbnail', models.ImageField(null=True, upload_to='thumbnails/')),
                ('clip_size', models.PositiveIntegerField(help_text='File size measured in bytes.', null=True)),
                ('thumbnail_size', models.PositiveIntegerField(help_text='Image size measured in bytes.', null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playbooks', to=settings.AUTH_USER_MODEL)),
                ('notes', models.ManyToManyField(related_name='playbooks', to='api.note')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playbooks', to='api.project')),
            ],
        ),
        migrations.CreateModel(
            name='PlayBookTakeaway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                ('playbook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playbook_takeaways', to='api.playbook')),
                ('takeaway', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.takeaway')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('playbook', 'takeaway')},
            },
        ),
        migrations.AddField(
            model_name='playbook',
            name='takeaways',
            field=models.ManyToManyField(related_name='playbooks', through='api.PlayBookTakeaway', to='api.takeaway'),
        ),
        migrations.AddField(
            model_name='playbook',
            name='workspace',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playbooks', to='api.workspace'),
        ),
        migrations.AlterUniqueTogether(
            name='playbook',
            unique_together={('title', 'project')},
        ),
    ]

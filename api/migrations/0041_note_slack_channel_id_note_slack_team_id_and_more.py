# Generated by Django 4.2.3 on 2024-06-25 10:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import secrets


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0040_asset_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='slack_channel_id',
            field=models.CharField(max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='note',
            name='slack_team_id',
            field=models.CharField(max_length=25, null=True),
        ),
        migrations.CreateModel(
            name='SlackOAuthState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(default=secrets.token_urlsafe, max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SlackMessageBuffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slack_channel_id', models.CharField(max_length=25)),
                ('slack_team_id', models.CharField(max_length=25)),
                ('slack_user', models.CharField(max_length=25)),
                ('message_text', models.TextField()),
                ('timestamp', models.DateTimeField()),
            ],
            options={
                'indexes': [models.Index(fields=['slack_channel_id', 'slack_team_id'], name='api_slackme_slack_c_09d51e_idx')],
            },
        ),
        migrations.CreateModel(
            name='SlackUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.CharField(max_length=255)),
                ('slack_user_id', models.CharField(max_length=35)),
                ('slack_team_id', models.CharField(max_length=35)),
                ('bot_user_token', models.CharField(blank=True, max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slack_users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'slack_team_id')},
            },
        ),
    ]

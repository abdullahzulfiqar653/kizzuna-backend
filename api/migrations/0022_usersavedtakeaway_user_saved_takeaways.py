# Generated by Django 4.2.3 on 2024-03-19 06:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_asset_block'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSavedTakeaway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('takeaway', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.takeaway')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='saved_takeaways',
            field=models.ManyToManyField(related_name='saved_by', through='api.UserSavedTakeaway', to='api.takeaway'),
        ),
    ]

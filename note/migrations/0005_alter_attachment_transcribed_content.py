# Generated by Django 4.2.3 on 2023-08-04 06:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("note", "0004_attachment_transcribed_content"),
    ]

    operations = [
        migrations.AlterField(
            model_name="attachment",
            name="transcribed_content",
            field=models.TextField(),
        ),
    ]

# Generated by Django 4.2.3 on 2024-08-30 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0056_contact_googlecalendarattendee_googlecalendarchannel_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='googlecalendarattendee',
            name='name',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
    ]
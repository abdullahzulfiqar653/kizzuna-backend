# Generated by Django 4.2.3 on 2023-10-01 11:29

from django.db import migrations, models

replace = {
    'open': 'Open',
    'onhold': 'Onhold',
    'close': 'Closed',
}

def replace_values(apps, schema_editor):
    Takeaway = apps.get_model('takeaway', 'Takeaway')
    for takeaway in Takeaway.objects.all():
        if takeaway.status is not None:
            takeaway.status = replace[takeaway.status]
        takeaway.save()

def revert_replace_values(apps, schema_editor):
    Takeaway = apps.get_model('takeaway', 'Takeaway')
    revert_replace = dict(map(reversed, replace.items()))
    for takeaway in Takeaway.takeawayects.all():
        if takeaway.status is not None:
            takeaway.status = revert_replace[takeaway.status]
        takeaway.save()


class Migration(migrations.Migration):

    dependencies = [
        ('takeaway', '0006_alter_takeaway_created_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='takeaway',
            name='sentiment',
        ),
        migrations.AlterField(
            model_name='takeaway',
            name='status',
            field=models.CharField(choices=[('Open', 'Open'), ('Onhold', 'Onhold'), ('Closed', 'Close')], default='Open', max_length=6),
        ),
        migrations.RunPython(
            code=replace_values, 
            reverse_code=revert_replace_values,
        ),
    ]
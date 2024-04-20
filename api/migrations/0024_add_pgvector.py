from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    dependencies = [("api", "0023_notequestion_created_at_notequestion_created_by")]

    operations = [
        VectorExtension(),
    ]

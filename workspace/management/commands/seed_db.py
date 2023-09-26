from django.core.management.base import BaseCommand
from seeders import seed  # Adjust the import based on your project structure

class Command(BaseCommand):
    help = "Seeds the database with initial fake data"

    def handle(self, *args, **kwargs):
        seed.run()
        self.stdout.write(self.style.SUCCESS("Database seeded!"))
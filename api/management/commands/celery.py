import shlex
import subprocess
import sys

from django.core.management.base import BaseCommand
from django.utils import autoreload


# Ref: https://stackoverflow.com/a/77668168/9577282
def restart_celery():
    celery_worker_cmd = "celery -A cradarai worker --beat"
    cmd = f'pkill -f "{celery_worker_cmd}"'
    if sys.platform == "win32":
        cmd = "taskkill /f /t /im celery.exe"

    subprocess.call(shlex.split(cmd))
    cmd = f"{celery_worker_cmd} -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
    subprocess.call(shlex.split(cmd))


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Starting celery worker with autoreload...")
        autoreload.run_with_reloader(restart_celery)

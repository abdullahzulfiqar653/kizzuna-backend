# Ref: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cradarai.settings")

app = Celery("cradarai")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "summarize-projects": {
        "task": "api.tasks.summarize_projects",
        "schedule": crontab(minute=0, hour=9, day_of_week=1),
    },
}

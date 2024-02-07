from celery import shared_task
from django.utils import translation

from api.ai.analyzer.note_analyzer import ExistingNoteAnalyzer, NewNoteAnalyzer
from api.ai.analyzer.project_summarizer import ProjectSummarizer
from api.models.note import Note


@shared_task
def summarize_projects():
    print("summarizing projects")
    project_summarizer = ProjectSummarizer()
    project_summarizer.summarize_all_projects()


@shared_task
def analyze_new_note(note_id):
    analyzer = NewNoteAnalyzer()

    note = Note.objects.get(id=note_id)
    note.is_analyzing = True
    note.save()

    with translation.override(note.project.language):
        analyzer.analyze(note)

    note.is_analyzing = False
    note.save()


@shared_task
def analyze_existing_note(note_id):
    analyzer = ExistingNoteAnalyzer()

    note = Note.objects.get(id=note_id)
    note.is_analyzing = True
    note.save()

    with translation.override(note.project.language):
        analyzer.analyze(note)

    note.is_analyzing = False
    note.save()

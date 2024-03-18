from celery import shared_task

from api.ai.analyzer.note_analyzer import ExistingNoteAnalyzer, NewNoteAnalyzer
from api.ai.analyzer.project_summarizer import ProjectSummarizer
from api.models.note import Note
from api.models.user import User


@shared_task
def summarize_projects():
    print("summarizing projects")
    bot = User.objects.get(username="bot@raijin.ai")
    project_summarizer = ProjectSummarizer()
    project_summarizer.summarize_all_projects(created_by=bot)


@shared_task
def analyze_new_note(note_id, user_id):
    print(f"analyzing new note {note_id} by {user_id}")
    analyzer = NewNoteAnalyzer()
    try:
        note = Note.objects.select_related("project__workspace").get(id=note_id)
    except Exception as e:
        print("Debug: Failed to connect to db")
        import traceback

        from django.db import connection

        traceback.print_exc()
        print(connection.queries)
        raise e
    note.is_analyzing = True
    note.save()

    user = User.objects.get(id=user_id)
    try:
        analyzer.analyze(note, user)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise e
    finally:
        note.is_analyzing = False
        note.save()


@shared_task
def analyze_existing_note(note_id, user_id):
    print("analyzing existing note")
    analyzer = ExistingNoteAnalyzer()

    note = Note.objects.select_related("project__workspace").get(id=note_id)
    note.is_analyzing = True
    note.save()

    user = User.objects.get(id=user_id)

    try:
        analyzer.analyze(note, user)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise e
    finally:
        note.is_analyzing = False
        note.save()

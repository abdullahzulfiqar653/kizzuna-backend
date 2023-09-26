from django.shortcuts import get_object_or_404, redirect
from note.models import Attachment

# from .transcribers import GoogleTranscriber
# transcriber = GoogleTranscriber()

# from .transcribers import WhisperTranscriber
# transcriber = WhisperTranscriber()

def transcribe_create(request, note_id, attachment_id):
    # attachment = get_object_or_404(Attachment, id=attachment_id)
    # filepath = attachment.file.path
    # filetype = attachment.file_type
    # transcript = transcriber.transcribe(filepath, filetype)
    # if transcript is not None:
    #     attachment.transcribed_content = transcript
    #     attachment.save()
    return redirect('attachment-detail', note_id=note_id, attachment_id=attachment_id)

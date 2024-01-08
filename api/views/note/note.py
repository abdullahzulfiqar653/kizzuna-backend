from django.db.models import Count
from rest_framework import exceptions, generics

from api.models.note import Note
from api.serializers.note import NoteSerializer


class NoteRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_queryset(self):
        return super().get_queryset().annotate(takeaway_count=Count("takeaways"))

    def retrieve(self, request, pk):
        note = Note.objects.filter(id=pk).first()
        if note is None or not note.project.users.contains(request.user):
            raise exceptions.NotFound("Report not found.")
        return super().retrieve(request, pk)


# def attachment_create(request, note_id):
#     if request.method == 'POST':
#         form = AttachmentForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = form.cleaned_data['file']
#             note = get_object_or_404(Note, id=note_id)
#             instance = form.save()
#             note.attachments.add(instance)

#             # # Upload to S3
#             # s3 = boto3.resource('s3')
#             # bucket_name = settings.AWS_STORAGE_BUCKET_NAME
#             # folder_name = 'note'
#             # file_key = f"{folder_name}/{file.name}"
#             # s3.Bucket(bucket_name).put_object(Key=file_key, Body=file)

#             return redirect('attachment-detail', note_id=note_id, attachment_id=instance.id)
#     else:
#         form = AttachmentForm()
#     return render(request, 'note_form.html', {'form': form})

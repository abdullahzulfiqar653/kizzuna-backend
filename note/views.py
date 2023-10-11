import json
from pprint import pprint
from textwrap import dedent

from django.db.models import Count
from django.shortcuts import get_object_or_404
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field, constr
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from note.models import Note
from note.serializers import NoteSerializer
from tag.models import Tag
from tag.serializers import TagSerializer
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer

from .models import Note

class TakeawaySchema(BaseModel):
    message: str = Field(description='message of the takeaway.')
    tags: list[constr(max_length=50)] = Field(description='Tags to be added to the takeaway.')

class TakeawayListSchema(BaseModel):
    takeaways: list[TakeawaySchema]

output_parser = PydanticOutputParser(pydantic_object=TakeawayListSchema)

prompt = PromptTemplate(
    input_variables=['takeaways'],
    template=dedent("""
        Given the following takeaway messages,
        add tags to each takeaway message.
        Give 3 - 5 tags for each message.
        {format_instructions}
                    
        {takeaways}
    """),
    partial_variables={
        'format_instructions': output_parser.get_format_instructions(),
    },
)
llm = ChatOpenAI()
chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser)

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

class NoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )

class NoteRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    
    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NoteTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    ordering_fields = [
        'created_at', 
        'created_by__first_name', 
        'created_by__last_name', 
        'title',
    ]
    ordering = ['created_at']
    search_fields = [
        'title',
        'created_by__username',
        'created_by__first_name',
        'created_by__last_name',
    ]

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get('report_id')
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise PermissionDenied
        return Takeaway.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise PermissionDenied
        request.data['note'] = note.id
        return super().create(request)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class NoteTagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get('report_id')
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise PermissionDenied
        return Tag.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise PermissionDenied
        request.data['note'] = note.id
        return super().create(request)
    
    def perform_create(self, serializer):
        report_id = self.kwargs.get('report_id')
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(self.request.user):
            raise PermissionDenied
        tag = serializer.save()
        note.tags.add(tag)

class NoteTagDestroyView(generics.DestroyAPIView):
    note_queryset = Note.objects.all()
    tag_queryset = Tag.objects.all()
    note_serializer_class = NoteSerializer
    tag_serializer_class = TagSerializer

    def destroy(self, request, report_id, tag_id):
        try:
            note = self.note_queryset.get(pk=report_id)
            tag = self.tag_queryset.get(pk=tag_id)
        except Note.DoesNotExist or Tag.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if not note.project.users.contains(request.user):
            raise PermissionDenied

        # Check if the tag is related to the note
        if note.tags.filter(pk=tag_id).exists():
            # Remove the association between note and tag
            note.tags.remove(tag)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"detail": "Tag is not associated with the specified report."},
                status=status.HTTP_400_BAD_REQUEST
            )

class NoteTakeawayTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)

        if note.is_auto_tagged:
            raise PermissionDenied('Report takeaways have already auto tagged.')

        data = {
            'takeaways': [
                {
                    'message': takeaway.title,
                }
                for takeaway in note.takeaways.all()
            ]
        }
        takeaways = json.dumps(data)

        try:
            results = chain.predict(takeaways=takeaways).dict()
            pprint(results)
        except:
            import traceback
            traceback.print_exc()
            return Response({'details': 'Failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        for takeaway_data in results['takeaways']:
            takeaway = note.takeaways.get(title=takeaway_data['message'])
            for tag_str in takeaway_data['tags']:
                tag, created = Tag.objects.get_or_create(name=tag_str)
                takeaway.tags.add(tag)

        note.is_auto_tagged = True
        note.save()

        return Response({'details': 'Successful'})

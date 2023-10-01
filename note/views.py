import json
from pprint import pprint
from textwrap import dedent

from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
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

from .forms import NoteForm
from .models import Note

# class NoteInsight(BaseModel):
#     summary: str = Field(description='Summary of the text.')
#     keywords: list[str] = Field(description='The list of relevant keywords of the text.')
#     takeaways: list[str] = Field(description='What are the main messages to take away from the text. Not more than 5 takeaways from the text.')


# output_parser = PydanticOutputParser(pydantic_object=NoteInsight)

# prompt = PromptTemplate(
#     input_variables=['text'],
#     template=dedent("""
#         Analyze the following text: {text}
#         {format_instructions}
#     """),
#     partial_variables={
#         'format_instructions': output_parser.get_format_instructions(),
#     },
# )
# llm = ChatOpenAI()
# chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser)

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


def note_list(request):
    notes = Note.objects.all()
    return render(request, 'note_list.html', {'notes': notes})

def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    return render(request, 'note_detail.html', {'note': note})

def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('note-list')
    else:
        form = NoteForm()
    return render(request, 'note_form.html', {'form': form})

def note_update(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('note-list')
    else:
        form = NoteForm(instance=note)
    return render(request, 'note_form.html', {'form': form})

def note_delete(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete()
        return redirect('note-list')
    return render(request, 'note_confirm_delete.html', {'note': note})

# def note_create_summary(request, note_id):
#     # AI goes here
#     note = get_object_or_404(Note, id=note_id)
#     text = f'{note.title}\n{note.content}'
#     insight = chain.predict(text=text).dict()
#     note.summary = insight['summary']
#     note.save()
#     for keyword in insight['keywords']:
#         tag = Tag(name=keyword)
#         tag.save()
#         note.tags.add(tag)
#     for takeaway_title in insight['takeaways']:
#         takeaway = Takeaway(title=takeaway_title)
#         takeaway.save()
#         note.takeaways.add(takeaway)
#     return render(request, 'note_detail.html', {'note': note})


# def attachment_list(request, note_id):
#     attachments = Attachment.objects.filter(note__id=note_id)
#     note = get_object_or_404(Note, id=note_id)
#     return render(request, 'attachment_list.html', {'attachments': attachments, 'note': note})

# def attachment_detail(request, note_id, attachment_id):
#     note = get_object_or_404(Note, id=note_id)
#     attachment = get_object_or_404(Attachment, id=attachment_id)

#     return render(request, 'attachment_detail.html', {'note': note, 'attachment': attachment})

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

class NoteTakeawayTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
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
        return Response({'details': 'Successful'})

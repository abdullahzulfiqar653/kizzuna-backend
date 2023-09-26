from textwrap import dedent
from threading import Thread
from time import time

from django.core.exceptions import PermissionDenied
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from rest_framework import generics, status
from rest_framework.response import Response

from note.models import Note
from note.serializers import NoteSerializer
from tag.models import Tag
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer
from transcriber.transcribers import WhisperTranscriber
from user.serializers import UserSerializer

from .forms import ProjectForm
from .models import Project

transcriber = WhisperTranscriber()


class NoteInsight(BaseModel):
    summary: str = Field(description='Summary of the text.')
    keywords: list[str] = Field(description='The list of relevant keywords of the text.')
    takeaways: list[str] = Field(description='What are the main messages to take away from the text. Not more than 5 takeaways from the text.')


output_parser = PydanticOutputParser(pydantic_object=NoteInsight)

prompt = PromptTemplate(
    input_variables=['text'],
    template=dedent("""
        Analyze the following text: {text}
        {format_instructions}
    """),
    partial_variables={
        'format_instructions': output_parser.get_format_instructions(),
    },
)
llm = ChatOpenAI()
chain = LLMChain(llm=llm, prompt=prompt, output_parser=output_parser)

def project_list(request):
    projects = Project.objects.all()
    return render(request, 'project_list.html', {'projects': projects})

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, 'project_detail.html', {'project': project})

def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect('project-list')
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})

def project_update(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project-list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_form.html', {'form': form})

def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        project.delete()
        return redirect('project-list')
    return render(request, 'project_confirm_delete.html', {'project': project})


class ProjectUserListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def list(self, request, project_id=None):
        project = get_object_or_404(Project, id=project_id)
       
        # TODO: Check permission
        if not project.users.contains(request.user):
            raise PermissionDenied

        users = project.users.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
class ProjectNoteListCreateView(generics.ListCreateAPIView):
    serializer_class = NoteSerializer

    def list(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
       
        # TODO: Check permission
        if not project.users.contains(request.user):
            raise PermissionDenied

        notes = project.notes.all().order_by('-created_at')
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)
    
    def get_serializer(self, *args, **kwargs):
        # Convert data to json if the request is multipart form
        data = kwargs.get('data')
        
        if data is None:
            return super().get_serializer(*args, **kwargs)

        if isinstance(data, QueryDict):
            data = data.dict()
            kwargs['data'] = data

        # Set project
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise PermissionDenied
        data['project'] = project_id

        # In multipart form, null will be treated as string instead of converting to None
        # We need to manually handle the null
        if data['revenue'] == 'null':
            data['revenue'] = None

        if data['file'] == 'null':
            data['file'] = None

        return super().get_serializer(*args, **kwargs)
    
    def perform_create(self, serializer):
        note = serializer.save(author=self.request.user)
        if note.file:
            thread = Thread(
                target=self.analyze,
                kwargs={'note': note},
            )
            thread.start()

    def transcribe(self, note):
        filepath = note.file.path
        filetype = note.file_type
        transcript = transcriber.transcribe(filepath, filetype)
        if transcript is not None:
            note.content = transcript
            note.save()

    def summarize(self, note):
        text = f'{note.title}\n{note.content}'
        insight = chain.predict(text=text).dict()
        note.summary = insight['summary']
        note.save()
        for keyword in insight['keywords']:
            tag, is_created = Tag.objects.get_or_create(name=keyword)
            note.tags.add(tag)
        for takeaway_title in insight['takeaways']:
            takeaway = Takeaway(title=takeaway_title, note=note)
            takeaway.save()


    def analyze(self, note):
        note.is_analyzing = True
        note.save()
        try:
            print('========> Start transcribing')
            start = time()
            self.transcribe(note)
            end = time()
            print(f'Elapsed time: {end - start} seconds')
            print('========> Start summarizing')
            self.summarize(note)
            print('========> End analyzing')
        except Exception as e:
            print(str(e))
        note.is_analyzing = False
        note.save()
    
class ProjectTakeawayListView(generics.ListAPIView):
    serializer_class = TakeawaySerializer

    def list(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
       
        # TODO: Check permission
        if not project.users.contains(request.user):
            raise PermissionDenied

        takeaways = Takeaway.objects.filter(note__project=project)
        serializer = TakeawaySerializer(takeaways, many=True)
        return Response(serializer.data)

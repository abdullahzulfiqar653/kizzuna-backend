import json
from pprint import pprint
from textwrap import dedent
from threading import Thread
from time import time

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field, constr
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from note.filters import NoteFilter
from note.models import Note
from note.serializers import NoteSerializer
from project.models import Project
from project.serializers import ProjectSerializer
from tag.models import Tag
from takeaway.filters import TakeawayFilter
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer
from transcriber.transcribers import OpenAITranscriber
from user.serializers import UserSerializer

from .forms import ProjectForm
from .models import Project

transcriber = OpenAITranscriber()


class NoteInsightSchema(BaseModel):
    summary: str = Field(description='Summary of the text.')
    keywords: list[constr(max_length=50)] = Field(description='The list of relevant keywords of the text.')
    takeaways: list[str] = Field(description='What are the main messages to take away from the text. Not more than 5 takeaways from the text.')
    sentiment: Note.Sentiment = Field(description='The sentiment of the text.')


output_parser = PydanticOutputParser(pydantic_object=NoteInsightSchema)

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

class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        return Project.objects.filter(workspace=workspace, users=auth_user)
    
    def create(self, request, *args, **kwargs):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise PermissionDenied('Cannot create more than 2 projects in one workspace.')
        return super().create(request, *args, **kwargs)

class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filterset_class = NoteFilter
    ordering_fields = [
        'created_at', 
        'takeaway_count', 
        'author__first_name', 
        'author__last_name', 
        'company_name',
        'title',
    ]
    search_fields = ['title']
    ordering = ['-created_at']

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise PermissionDenied
        return (
            project.notes
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )
    
    def get_project_id(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise PermissionDenied
        return project_id
    
    def to_dict(self, form_data):
        data_file = form_data.get('data')
        if not isinstance(data_file, UploadedFile):
            raise serializers.ValidationError('`data` field must be a blob.')
        data = json.load(data_file)
        data['file'] = form_data.get('file')
        return data

    
    def get_serializer(self, *args, **kwargs):
        # Convert data to json if the request is multipart form
        data = kwargs.get('data')
        
        if data is None:
            # If it is not POST request, data is None
            return super().get_serializer(*args, **kwargs)

        if isinstance(data, QueryDict):
            kwargs['data'] = self.to_dict(data)
            data = kwargs['data']

        # Set project
        data['project'] = self.get_project_id()

        # In multipart form, null will be treated as string instead of converting to None
        # We need to manually handle the null
        if 'revenue' not in data or data['revenue'] == 'null':
            data['revenue'] = None

        if 'file' not in data or data['file'] == 'null':
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
        pprint(insight)
        note.summary = insight['summary']
        note.sentiment = insight['sentiment']
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
    filterset_class = TakeawayFilter
    ordering_fields = [
        'created_at', 
        'created_by__first_name', 
        'created_by__last_name', 
        'title',
    ]
    search_fields = ['title']
    ordering = ['-created_at']

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
       
        # TODO: Check permission
        if not project.users.contains(self.request.user):
            raise PermissionDenied

        return Takeaway.objects.filter(note__project=project)

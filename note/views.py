import json
from pprint import pprint
from textwrap import dedent

from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field, constr
from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from note.models import Note
from note.serializers import NoteSerializer
from tag.models import Keyword, Tag
from tag.serializers import KeywordSerializer
from takeaway.models import Highlight, Takeaway
from takeaway.serializers import HighlightSerializer, TakeawaySerializer

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


class NoteRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    
    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )

    def retrieve(self, request, pk):
        note = Note.objects.filter(id=pk).first()
        if note is None or not note.project.users.contains(request.user):
            raise exceptions.NotFound('Report not found.')
        return super().retrieve(request, pk)

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
            raise exceptions.PermissionDenied
        return Takeaway.objects.filter(note=note)
      
    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data['note'] = note.id
        return super().create(request)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class NoteHighlightCreateView(generics.CreateAPIView):
    queryset = Highlight.objects.all()
    serializer_class = HighlightSerializer


class NoteKeywordListCreateView(generics.ListCreateAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get('report_id')
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise exceptions.PermissionDenied
        return Keyword.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data['note'] = note.id
        return super().create(request)
    
    def perform_create(self, serializer):
        report_id = self.kwargs.get('report_id')
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        keyword = serializer.save()
        note.keywords.add(keyword)

class NoteKeywordDestroyView(generics.DestroyAPIView):
    serializer_class = KeywordSerializer

    def destroy(self, request, report_id, keyword_id):
        note = Note.objects.filter(pk=report_id, project__users=request.user).first()
        if note is None:
            raise exceptions.NotFound(f'Report {report_id} not found.')
        
        keyword = note.keywords.filter(pk=keyword_id).first()
        if keyword is None:
            raise exceptions.NotFound(f'Keyword {keyword_id} not found.')
        
        note.keywords.remove(keyword)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses={200: None})
class NoteTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)

        if note.is_auto_tagged:
            raise exceptions.PermissionDenied('Report takeaways have already auto tagged.')

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

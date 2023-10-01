import random
import string

from django.contrib.auth.models import User as AuthUser
from django.core.exceptions import ValidationError
from django.db import models
from shortuuid.django_fields import ShortUUIDField

from project.models import Project
from tag.models import Tag
from user.models import User
from workspace.models import Workspace


def validate_file_size(value):
    max_size = 20 * 1024 * 1024  # 20 MB
    if value.size > max_size:
        raise ValidationError('File size cannot exceed 20 MB.')

def validate_file_type(value):
    allowed_extensions = ['pdf', 'mp3', 'wav']
    ext = value.name.split('.')[-1]
    if ext.lower() not in allowed_extensions:
        raise ValidationError('Only PDF, MP3, and WAV files are allowed.')

class Note(models.Model):
    class Revenue(models.TextChoices):
        LOW = 'Low'
        MEDIUM = 'Medium'
        HIGH = 'High'

    class FileType(models.TextChoices):
        PDF = 'pdf'
        MP3 = 'mp3'
        WAV = 'wav'

    class Sentiment(models.TextChoices):
        POSITIVE = 'Positive'
        NEUTRAL = 'Neutral'
        NEGATIVE = 'Negative'
        
    id = ShortUUIDField(length=12, max_length=12, primary_key=True)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name='notes')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='notes')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='notes')
    tags = models.ManyToManyField(Tag, blank=True)
    company_name = models.CharField(max_length=255)
    revenue = models.CharField(max_length=6, choices=Revenue.choices, null=True)
    user_participants = models.ManyToManyField(User)
    description = models.TextField()
    type = models.CharField(max_length=255)
    is_published = models.BooleanField(default=False)
    code = models.CharField(max_length=5)
    takeaway_sequence = models.IntegerField(default=0)

    file = models.FileField(upload_to='attachments/', validators=[validate_file_size, validate_file_type], null=True)
    file_type = models.CharField(max_length=3, choices=FileType.choices, null=True)
    is_analyzing = models.BooleanField(default=False)
    content = models.TextField()
    summary = models.TextField()
    keywords = models.TextField()
    sentiment = models.CharField(max_length=8, choices=Sentiment.choices, null=True)
    
    class Meta:
        unique_together = [
            ['workspace', 'code'],
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file and self.file.name:
            self.file_type = self.file.name.split('.')[-1].lower()
        else: 
            self.file_type = None
        self.workspace = self.project.workspace
        if not self.code:
            # Generate random code
            chars = string.ascii_letters[26:]
            self.code = ''.join(random.choice(chars) for _ in range(3))
        super().save(*args, **kwargs)
    
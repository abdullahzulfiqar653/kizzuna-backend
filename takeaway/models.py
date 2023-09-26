from django.contrib.auth.models import User
from django.db import models
from shortuuid.django_fields import ShortUUIDField

from tag.models import Tag


class Takeaway(models.Model):
    class Sentiment(models.TextChoices):
        POSITIVE = 'positive'
        NEUTRAL = 'neutral'
        NEGATIVE = 'negative'
        
    class Status(models.TextChoices):
        OPEN = 'open'
        ONHOLD = 'onhold'
        CLOSE = 'close'
    
    id = ShortUUIDField(length=12, max_length=12, primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True)
    sentiment = models.CharField(max_length=8, choices=Sentiment.choices, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='takeaways', null=True)
    upvoted_by = models.ManyToManyField(User)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    note = models.ForeignKey('note.Note', on_delete=models.CASCADE, related_name='takeaways')
    code = models.CharField(max_length=10, unique=True)
    

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.code == '':
            self.code = f'{self.note.code}-{self.note.takeaway_sequence + 1}'
            note = self.note
            note.takeaway_sequence += 1
            note.save()
        super().save(*args, **kwargs)

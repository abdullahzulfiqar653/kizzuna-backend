from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'code', 'content', 'author', 'tags', 'project']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Exclude the field 'code' when updating an object
        if self.instance and self.instance.code:
            self.fields.pop('code')

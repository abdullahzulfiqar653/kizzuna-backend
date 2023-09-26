from django import forms
from .models import Takeaway

class TakeawayForm(forms.ModelForm):
    class Meta:
        model = Takeaway
        fields = ['note', 'title', 'description', 'tags']

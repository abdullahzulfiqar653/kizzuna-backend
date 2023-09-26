from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    # Add or modify fields here

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']  # 'email' field is now 

    def save(self, commit=True):
        user = super().save(commit=False)
        user.enmail = self.cleaned_data['email']  # clean email
        user.username = self.cleaned_data['email']  # Set username as email
        if commit:
            user.save()
        return user
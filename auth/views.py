# auth/views.py
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Authenticate the user
            user = form.get_user()
            auth_login(request, user)
            # Set session variables
            request.session['current_user_id'] = user.id
            request.session['current_workspace_id'] = None
            request.session['current_project_id'] = None
            # Redirect to a specific page after successful login
            return redirect('home')  # Change 'home' to the desired URL name
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'login.html', {'form': form})  # Updated template name

def logout(request):
    auth_logout(request)
    return redirect('login')

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Process password reset logic here (send email, etc.)
            messages.success(request, 'Password reset email sent.')
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})  # Updated template name

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            # Set session variables
            request.session['current_workspace_id'] = None
            request.session['current_project_id'] = None
            # Redirect to a specific page after successful signup
            return redirect('home')  # Change 'home' to the desired URL name
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})  # Updated template name
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def protected(request):
    return render(request, 'home/protected.html')

def index(request):
    return render(request, 'home/waterfall.html')

@login_required
def home(request):

    current_user_id = request.user.id

    return render(request, 'home/waterfall.html', {'current_user_id': current_user_id})
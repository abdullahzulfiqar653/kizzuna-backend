from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, status
from rest_framework.response import Response

from tag.models import Tag
from tag.serializers import TagSerializer

from .forms import TakeawayForm
from .models import Takeaway
from .serializers import TakeawaySerializer


@login_required
def takeaway_list(request):
    takeaways = Takeaway.objects.all()
    return render(request, 'takeaway_list.html', {'takeaways': takeaways})

@login_required
def takeaway_detail(request, takeaway_id):
    takeaway = get_object_or_404(Takeaway, id=takeaway_id)
    return render(request, 'takeaway_detail.html', {'takeaway': takeaway})

@login_required
def takeaway_create(request):
    if request.method == 'POST':
        form = TakeawayForm(request.POST)
        if form.is_valid():
            import ipdb; ipdb.set_trace()
            takeaway = form.instance
            takeaway.created_by = request.user
            takeaway.save()
            return redirect('takeaway-list')
    else:
        form = TakeawayForm()
    return render(request, 'takeaway_form.html', {'form': form})

@login_required
def takeaway_update(request, takeaway_id):
    takeaway = get_object_or_404(Takeaway, id=takeaway_id)
    if request.method == 'POST':
        form = TakeawayForm(request.POST, instance=takeaway)
        if form.is_valid():
            form.save()
            return redirect('takeaway-list')
    else:
        form = TakeawayForm(instance=takeaway)
    return render(request, 'takeaway_form.html', {'form': form})

@login_required
def takeaway_delete(request, takeaway_id):
    takeaway = get_object_or_404(Takeaway, id=takeaway_id)
    if request.method == 'POST':
        takeaway.delete()
        return redirect('takeaway-list')
    return render(request, 'takeaway_confirm_delete.html', {'takeaway': takeaway})

class TakeawayTagCreateView(generics.CreateAPIView):
    serializer_class = TagSerializer

    def create(self, request, takeaway_id):
        takeaway = get_object_or_404(Takeaway, id=takeaway_id)
        project = takeaway.note.project
        if not project.users.contains(request.user):
            raise PermissionDenied
        
        serializer = TagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        takeaway.tags.add(tag)
        return Response(serializer.data)


class TakeawayTagDestroyView(generics.DestroyAPIView):
    takeaway_queryset = Takeaway.objects.all()
    tag_queryset = Tag.objects.all()
    takeaway_serializer_class = TakeawaySerializer
    tag_serializer_class = TagSerializer

    def destroy(self, request, takeaway_id, tag_id):
        try:
            takeaway = self.takeaway_queryset.get(pk=takeaway_id)
            tag = self.tag_queryset.get(pk=tag_id)
        except Takeaway.DoesNotExist or Tag.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if not takeaway.note.project.users.contains(request.user):
            raise PermissionDenied

        # Check if the tag is related to the takeaway
        if takeaway.tags.filter(pk=tag_id).exists():
            # Remove the association between takeaway and tag
            takeaway.tags.remove(tag)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"detail": "Tag is not associated with the specified takeaway."},
                status=status.HTTP_400_BAD_REQUEST
            )

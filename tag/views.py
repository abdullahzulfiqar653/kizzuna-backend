from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, status
from rest_framework.response import Response

from tag.models import Tag
from tag.serializers import TagSerializer

from .forms import TagForm
from .models import Tag


def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'tag_list.html', {'tags': tags})

def tag_detail(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    return render(request, 'tag_detail.html', {'tag': tag})

def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tag-list')
    else:
        form = TagForm()
    return render(request, 'tag_form.html', {'form': form})

def tag_update(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect('tag-list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'tag_form.html', {'form': form})

def tag_delete(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        return redirect('tag-list')
    return render(request, 'tag_confirm_delete.html', {'tag': tag})

class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class TagRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

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

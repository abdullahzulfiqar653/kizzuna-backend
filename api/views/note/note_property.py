from rest_framework import exceptions, generics

from api.models.note_property import NoteProperty
from api.serializers.note_property import NotePropertySerializer


class NotePropertyListView(generics.ListAPIView):
    queryset = NoteProperty.objects.all()
    serializer_class = NotePropertySerializer
    ordering = ["property__order"]

    def get_queryset(self):
        return NoteProperty.objects.filter(note=self.request.note)

    def list(self, request, *args, **kwargs):
        missing_properties = request.note.project.properties.exclude(
            note_properties__note=request.note
        )
        NoteProperty.objects.bulk_create(
            [
                NoteProperty(note=request.note, property=property)
                for property in missing_properties
            ]
        )
        return super().list(request, *args, **kwargs)


class NotePropertyUpdateView(generics.UpdateAPIView):
    queryset = NoteProperty.objects.all()
    serializer_class = NotePropertySerializer

    def get_queryset(self):
        return NoteProperty.objects.filter(note=self.request.note)

    def get_object(self):
        property_id = self.kwargs.get("property_id")
        property = self.request.note.project.properties.filter(id=property_id).first()
        if property is None:
            raise exceptions.NotFound(f"Property {property_id} not found")

        note_property = NoteProperty.objects.filter(
            note=self.request.note, property=property
        ).first()
        if note_property is None:
            note_property = NoteProperty.objects.create(
                note=self.request.note, property=property
            )
        return note_property

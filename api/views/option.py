from rest_framework import generics

from api.models.option import Option
from api.serializers.option import OptionSerializer


class OptionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

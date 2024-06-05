import re

from drf_spectacular.utils import extend_schema
from rest_framework import generics, response

from api.models.option import Option
from api.models.property import Property
from api.serializers.property import PropertySerializer


class PropertyRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertySerializer
    queryset = Property.objects.all()


def increment_copy_number(name, existing_names):
    existing_names = set(existing_names)
    if name not in existing_names:
        return name

    # Matches base name followed by optional "copy" and an optional number if preceded by "copy"
    pattern = r"^(.*?) (copy)?(?: ((?<=copy )\d+))?$"
    regex = re.compile(pattern)

    # Extract base name
    match = regex.match(name)
    if match:
        base_name = match.group(1)
    else:
        base_name = name

    # Increment copy number
    while name in existing_names:
        match = regex.match(name)
        if match is None:
            name = f"{base_name} copy"
        elif match.group(3):
            copy_number = int(match.group(3)) + 1
            name = f"{base_name} copy {copy_number}"
        else:
            name = f"{base_name} copy 2"
    return name


@extend_schema(request=None)
class PropertyDuplicateAPIView(generics.CreateAPIView):
    serializer_class = PropertySerializer
    queryset = Property.objects.all()

    def post(self, request, property_id):
        property = request.property
        options = list(property.options.all())
        existing_propertie_names = property.project.properties.values_list(
            "name", flat=True
        )

        property.pk = None
        property.name = increment_copy_number(property.name, existing_propertie_names)
        property.save()
        options_to_create = []
        for option in options:
            option.pk = None
            option.property = property
            options_to_create.append(option)
        Option.objects.bulk_create(options_to_create)
        serializer = self.get_serializer(property)
        return response.Response(serializer.data)

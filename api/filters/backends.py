from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from pgvector.django import MaxInnerProduct
from rest_framework.compat import coreapi, coreschema
from rest_framework.filters import BaseFilterBackend

from api.ai.embedder import embedder


class QueryFilter(BaseFilterBackend):
    query_param = "query"
    query_title = _("Query")
    query_description = _("A query term to search semantically.")

    def get_query_field(self, view, request):
        return getattr(view, "query_field", None)

    def get_query_string(self, request):
        return request.query_params.get(self.query_param, "")

    def filter_queryset(self, request, queryset, view):
        query_field = self.get_query_field(view, request)
        query_string = self.get_query_string(request)
        if not query_field or not query_string:
            return queryset
        query_vector = embedder.embed_query(query_string)
        return queryset.order_by(MaxInnerProduct(query_field, query_vector))

    def get_schema_fields(self, view):
        if self.get_query_field(view, None) is None:
            return []

        assert (
            coreapi is not None
        ), "coreapi must be installed to use `get_schema_fields()`"
        assert (
            coreschema is not None
        ), "coreschema must be installed to use `get_schema_fields()`"
        return [
            coreapi.Field(
                name=self.query_param,
                required=False,
                location="query",
                schema=coreschema.String(
                    title=force_str(self.query_title),
                    description=force_str(self.query_description),
                ),
            )
        ]

    def get_schema_operation_parameters(self, view):
        if self.get_query_field(view, None) is None:
            return []

        return [
            {
                "name": self.query_param,
                "required": False,
                "in": "query",
                "description": force_str(self.query_description),
                "schema": {
                    "type": "string",
                },
            },
        ]

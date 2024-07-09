from rest_framework import generics

from api.permissions import IsWorkspaceOwner
from api.serializers.billing_portal_session import (
    StripeBillingPortalSessionCreateSerializer,
)


class StripeBillingPortalSessionCreateView(generics.CreateAPIView):
    serializer_class = StripeBillingPortalSessionCreateSerializer
    permission_classes = [IsWorkspaceOwner]

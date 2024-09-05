from rest_framework import generics, permissions

from api.integrations.google import google_flow
from api.serializers.integrations.google.auth.url import GoogleAuthUrlSerializer


class GoogleAuthRetrieveView(generics.RetrieveAPIView):
    serializer_class = GoogleAuthUrlSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        state = self.request.query_params.get("state")
        authorization_url, state = google_flow.authorization_url(
            access_type="offline", prompt="consent", state=state
        )
        return {"authorization_url": authorization_url}

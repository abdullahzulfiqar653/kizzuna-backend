from rest_framework import generics, permissions

from api.integrations.google import google_flow, google_verification_flow
from api.serializers.integrations.google.auth.auth import GoogleAuthUrlSerializer


class GoogleAuthRetrieveView(generics.RetrieveAPIView):
    serializer_class = GoogleAuthUrlSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        state = self.request.query_params.get("state")
        is_google = self.request.query_params.get("google", False)
        if is_google:
            # TODO: Remove this after verifying the flow
            authorization_url, state = google_verification_flow.authorization_url(
                access_type="offline", prompt="consent", state=state
            )
        else:
            authorization_url, state = google_flow.authorization_url(
                access_type="offline", prompt="consent", state=state
            )
        return {"authorization_url": authorization_url}

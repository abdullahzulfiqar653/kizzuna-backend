import google_auth_oauthlib.flow
from django.conf import settings

google_flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    settings.GOOGLE_CLIENT_SECRET_FILE,
    scopes=settings.GOOGLE_SCOPES,
    redirect_uri=settings.GOOGLE_REDIRECT_URI,
)

# TODO: Remove this after verifying the flow
google_verification_flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    settings.GOOGLE_VERIFICATION_CLIENT_SECRET_FILE,
    scopes=settings.GOOGLE_SCOPES,
    redirect_uri=settings.GOOGLE_REDIRECT_URI,
)

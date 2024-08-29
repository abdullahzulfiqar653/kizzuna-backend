from django.conf import settings

from api.integrations.generic_client import GenericAPIClient

recall_base_url = "https://us-west-2.recall.ai/api"
recall = GenericAPIClient(
    recall_base_url,
    headers={"Authorization": f"Token {settings.RECALLAI_API_KEY}"},
)

import stripe
from rest_framework import serializers

from api.stripe import stripe


class StripeBillingPortalSessionCreateSerializer(serializers.Serializer):
    url = serializers.URLField(
        help_text="Redirect URL to return after Stripe portal session, also used to return the stripe portal URL"
    )
    client_secret = serializers.CharField(read_only=True)

    def create(self, validated_data):
        request = self.context.get("request")
        workspace, user = request.workspace, request.user
        customer = workspace.get_stripe_customer_id(user)
        try:
            client_secret = url = None
            if getattr(workspace, "subscription", None):
                session = stripe.billing_portal.Session.create(
                    customer=customer,
                    return_url=validated_data["url"],
                )
                url = session.url
            else:
                session = stripe.CustomerSession.create(
                    customer=customer,
                    components={"pricing_table": {"enabled": True}},
                )
                client_secret = session.client_secret
            return {"url": url, "client_secret": client_secret}
        except Exception as e:
            print(e)
            raise serializers.ValidationError(
                "Failed to create Stripe customer billing portal session"
            )

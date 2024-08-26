from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.stripe_price import StripePrice
from api.models.stripe_product import StripeProduct
from api.models.stripe_subscription import StripeSubscription
from api.stripe import stripe


class StripeWebhookView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        request=None,
        responses={status.HTTP_200_OK: None, status.HTTP_400_BAD_REQUEST: None},
    )
    def post(self, request):
        event = None
        payload = request.body
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET_KEY

        def get_date(date):
            # Convert timestamp to UTC datetime
            return timezone.datetime.fromtimestamp(date, tz=timezone.timezone.utc)

        def is_free_trial(date):
            return (
                False
                if date is None
                else get_date(date) > timezone.now().astimezone(timezone.utc)
            )

        # Authenticate stripe request
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handling events
        match event["type"]:
            case "customer.subscription.created":
                subscription = event["data"]["object"]
                # Fetch customer details
                customer = stripe.Customer.retrieve(subscription["customer"])
                StripeSubscription.objects.update_or_create(
                    id=subscription["id"],
                    defaults={
                        "user_id": customer["metadata"]["user_id"],
                        "product_id": subscription["plan"]["product"],
                        "workspace_id": customer["metadata"]["workspace_id"],
                        "end_at": get_date(subscription["current_period_end"]),
                    },
                )
            case "customer.subscription.updated":
                # This will be called from billing portal
                subscription = event["data"]["object"]
                sub, _ = StripeSubscription.objects.update_or_create(
                    id=subscription["id"],
                    defaults={
                        "status": subscription["status"],
                        "product_id": subscription["plan"]["product"],
                        "end_at": get_date(subscription["current_period_end"]),
                        "is_free_trial": is_free_trial(subscription["trial_end"]),
                    },
                )

                # TODO: will send this to mixpanel
                if subscription["cancel_at_period_end"]:
                    time_of_cancellation = subscription["canceled_at"]
                    will_cancelled_at = subscription["cancel_at"]
                    comment = subscription["cancellation_details"]["comment"]
                    feedback = subscription["cancellation_details"]["feedback"]
            case "customer.subscription.deleted":
                subscription = event["data"]["object"]
                if not subscription["cancel_at_period_end"]:
                    StripeSubscription.objects.filter(id=subscription["id"]).delete()
            case "customer.subscription.resumed":
                subscription = event["data"]["object"]
                # Attempt to update an existing subscription
                StripeSubscription.objects.filter(id=subscription["id"]).update(
                    status=subscription["status"],
                    product_id=subscription["plan"]["product"],
                    end_at=get_date(subscription["current_period_end"]),
                    is_free_trial=is_free_trial(subscription["trial_end"]),
                )
            case "customer.subscription.paused":
                subscription = event["data"]["object"]
                # Attempt to update an existing subscription
                StripeSubscription.objects.filter(id=subscription["id"]).update(
                    status=subscription["status"],
                    product_id=subscription["plan"]["product"],
                    end_at=get_date(subscription["current_period_end"]),
                    is_free_trial=is_free_trial(subscription["trial_end"]),
                )
            case "customer.subscription.trial_will_end":
                pass
            case "checkout.session.completed":
                pass
            case "product.created":
                StripeProduct.update_or_create(event["data"]["object"])
            case "product.updated":
                StripeProduct.update_or_create(event["data"]["object"])
            case "product.deleted":
                StripeProduct.objects.filter(id=event["data"]["object"]["id"]).delete()
            case "price.created":
                StripePrice.update_or_create(event["data"]["object"])
            case "price.updated":
                StripePrice.update_or_create(event["data"]["object"])
            case "price.deleted":
                StripePrice.objects.filter(id=event["data"]["object"]["id"]).delete()

        return Response(status=status.HTTP_200_OK)

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from api.models.stripe_subscription import StripeSubscription
from api.models.workspace import Workspace
from api.stripe import stripe


@admin.register(StripeSubscription)
class StripeSubscriptionAdmin(admin.ModelAdmin):
    list_filter = ("status", "is_free_trial")
    list_display = (
        "id",
        "workspace",
        "product",
        "user",
        "started_at",
        "end_at",
        "status",
        "is_free_trial",
    )
    search_fields = (
        "id",
        "workspace__name",
        "product__name",
        "user__username",
        "user__email",
    )
    readonly_fields = ["id"]
    ordering = ("-started_at",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("workspace", "product", "user")
        return queryset

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync/",
                self.admin_site.admin_view(self.sync_now),
                name="stripesubscription_sync",
            ),
        ]
        return custom_urls + urls

    def sync_now(self, request):
        workspaces = Workspace.objects.filter(subscription__isnull=True)
        try:
            for workspace in workspaces:
                owner_user = workspace.workspace_users.filter(role="Owner").first().user
                workspace.usage_type = Workspace.UsageType.WORK
                workspace.save()
                stripe.Subscription.create(
                    customer=workspace.get_stripe_customer_id(owner_user),
                    items=[{"price": workspace.get_product_price_id()}],
                    metadata={"workspace_id": workspace.id, "user_id": owner_user.id},
                    trial_period_days=14,
                )

            messages.success(
                request,
                f"subscriptions for all workspaces activated with {Workspace.UsageType.WORK} usage type.",
            )
        except Exception as e:
            messages.error(
                request,
                f"Something went wrong, Please make sure that you mapped stripe products with usage type. Error: {e}",
            )
        return HttpResponseRedirect(reverse("admin:api_stripesubscription_changelist"))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        sync_url = reverse("admin:stripesubscription_sync")
        extra_context["sync_url"] = sync_url
        return super().changelist_view(request, extra_context=extra_context)

    change_list_template = "admin/stripe_subscription_changelist.html"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

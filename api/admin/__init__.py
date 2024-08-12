from django.contrib import admin
from django.contrib.auth.models import Group
from django_celery_results.admin import GroupResultAdmin, TaskResultAdmin
from django_celery_results.models import GroupResult, TaskResult

from api.admin.feature import FeatureAdmin
from api.admin.product_feature import ProductFeatureAdmin
from api.admin.stripe_price import StripePrice
from api.admin.stripe_product import StripeProductAdmin
from api.admin.stripe_subscription import StripeSubscriptionAdmin
from api.admin.workspace import WorkspaceAdmin

# This is to load the admins so that we can unregister them later
GroupResultAdmin
TaskResultAdmin

# Unregistering models
admin.site.unregister(Group)
admin.site.unregister(TaskResult)
admin.site.unregister(GroupResult)

__all__ = [
    "FeatureAdmin",
    "ProductFeatureAdmin",
    "StripePrice",
    "StripeProductAdmin",
    "StripeSubscriptionAdmin",
    "WorkspaceAdmin",
]

from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project

default_takeaway_types = [
    {
        "name": "Pain Point",
        "definition": "A specific problem or frustration experienced by a customer or user when using a product or service.",
    },
    {
        "name": "Aha Moment",
        "definition": "A point in time when a customer or user suddenly realizes the value or benefit of a product or service, leading to increased engagement and satisfaction.",
    },
    {
        "name": "Price Mention",
        "definition": "A reference made by a customer or user to the cost or pricing of a product or service, which may indicate price sensitivity or a willingness to pay.",
    },
    {
        "name": "Timeline Mention",
        "definition": "A reference made by a customer or user to the time frame for implementation of their goals and plans, and when they need to eliminate their challenges.",
    },
    {
        "name": "Stakeholder Mention",
        "definition": "A reference made by a customer to the person in the organization who will help champion and/or decide to make a purchase.",
    },
    {
        "name": "Customer Objection",
        "definition": "A point in time when a customer or user challenges the benefits of a product or service.",
    },
    {
        "name": "Solution Presentation",
        "definition": "A point in the sales call when the sales rep is presenting the product or solution to the customer.",
    },
    {
        "name": "Objection Handling",
        "definition": "A response from the sales rep to a customer objection.",
    },
    {
        "name": "Buying Signal/Aha Moment",
        "definition": "A point in time when a customer or user suddenly realizes the value or benefit of a product or service, leading to increased likelihood of a sales deal.",
    },
    {
        "name": "Churn Signal",
        "definition": "An indication that a customer or user is unlikely to proceed with a sale, often based on a decrease in engagement or satisfaction.",
    },
    {
        "name": "Contract Details Mention",
        "definition": "A point in time when a customer mentions any specific details regarding the final contract, e.g. pricing, payment schedules, contract length etc.",
    },
]

class TakeawayType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    definition = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="takeaway_types", editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]

    def __str__(self) -> str:
        return self.name

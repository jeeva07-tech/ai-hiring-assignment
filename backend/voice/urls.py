from django.urls import path

from .views import (
    CreateHunarCallView,
    HunarAgentsView,
    HunarCallDetailView,
    HunarWebhookView,
)


urlpatterns = [
    path(
        "agents/",
        HunarAgentsView.as_view(),
        name="hunar-agents",
    ),
    path(
        "calls/",
        CreateHunarCallView.as_view(),
        name="hunar-create-call",
    ),
    path(
        "calls/<str:call_id>/",
        HunarCallDetailView.as_view(),
        name="hunar-call-detail",
    ),
    path(
        "webhooks/hunar/",
        HunarWebhookView.as_view(),
        name="hunar-webhook",
    ),
]
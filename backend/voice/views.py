import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from candidates.models import Candidate, Interview
from hiring.models import Job

from .helpers import verify_hunar_webhook_signature
from .services import HunarAPIError, HunarService


class HunarAgentsView(APIView):
    """
    GET /api/voice/agents/

    Fetch available Hunar AI voice agents.
    """

    def get(self, request):
        try:
            service = HunarService()

            agents = service.list_agents()

            return Response(
                agents,
                status=status.HTTP_200_OK,
            )

        except HunarAPIError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class CreateHunarCallView(APIView):
    """
    POST /api/voice/calls/

    Create a Hunar voice call and save the interview
    information in PostgreSQL.
    """

    def post(self, request):
        required_fields = [
            "job_id",
            "agent_id",
            "callee_name",
            "mobile_number",
        ]

        missing_fields = [
            field
            for field in required_fields
            if not request.data.get(field)
        ]

        if missing_fields:
            return Response(
                {
                    "error": "Missing required fields",
                    "fields": missing_fields,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        job_id = request.data["job_id"]
        agent_id = request.data["agent_id"]
        callee_name = request.data["callee_name"]
        mobile_number = request.data["mobile_number"]

        custom_data = request.data.get("custom_data") or {}

        # Get the job from PostgreSQL
        job = get_object_or_404(
            Job,
            id=job_id,
        )

        try:
            # -------------------------------------------------
            # Build Hunar webhook callback configuration
            # -------------------------------------------------

            webhook_base_url = getattr(
                settings,
                "HUNAR_WEBHOOK_BASE_URL",
                "",
            ).rstrip("/")

            callback_config = None

            if webhook_base_url:
                webhook_url = (
                    f"{webhook_base_url}"
                    "/api/voice/webhooks/hunar/"
                )

                callback_config = {
                    "call_status_callback_url": webhook_url,
                    "call_recording_callback_url": webhook_url,
                    "call_result_callback_url": webhook_url,
                    "call_summary_callback_url": webhook_url,
                }

            # -------------------------------------------------
            # Create Hunar call
            # -------------------------------------------------

            service = HunarService()

            call = service.create_call(
                agent_id=agent_id,
                callee_name=callee_name,
                mobile_number=mobile_number,
                custom_data=custom_data,
                request_id=request.data.get(
                    "request_id"
                ),
                timezone=request.data.get(
                    "timezone",
                    "Asia/Kolkata",
                ),
                callback_config=callback_config,
            )

            # -------------------------------------------------
            # Create candidate in PostgreSQL
            # -------------------------------------------------

            candidate = Candidate.objects.create(
                job=job,
                name=callee_name,
                mobile_number=mobile_number,
            )

            # -------------------------------------------------
            # Create interview record
            # -------------------------------------------------

            interview = Interview.objects.create(
                candidate=candidate,
                job=job,
                hunar_agent_id=agent_id,
                call_id=call.get("id"),
                request_id=call.get("request_id"),
                status=call.get(
                    "status",
                    "NOT_STARTED",
                ),
                lifecycle_status=call.get(
                    "lifecycle_status"
                ),
                custom_data=custom_data,
                raw_payload=call,
            )

            return Response(
                {
                    "message": (
                        "Hunar call created successfully."
                    ),
                    "call": call,
                    "candidate": {
                        "id": candidate.id,
                        "name": candidate.name,
                        "job_id": candidate.job_id,
                    },
                    "interview": {
                        "id": interview.id,
                        "call_id": interview.call_id,
                        "status": interview.status,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except HunarAPIError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class HunarCallDetailView(APIView):
    """
    GET /api/voice/calls/<call_id>/

    Get the current status and details of a Hunar voice call.
    """

    def get(self, request, call_id):
        try:
            service = HunarService()

            call = service.get_call(call_id)

            return Response(
                call,
                status=status.HTTP_200_OK,
            )

        except HunarAPIError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class HunarWebhookView(APIView):
    """
    POST /api/voice/webhooks/hunar/

    Receives Hunar webhook events and updates the Interview.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # -------------------------------------------------
        # Get raw request body
        # -------------------------------------------------

        request_body = request.body

        # -------------------------------------------------
        # Get Hunar webhook security headers
        # -------------------------------------------------

        signature = request.headers.get(
            "X-Hunar-Signature"
        )

        timestamp = request.headers.get(
            "X-Hunar-Timestamp"
        )

        # -------------------------------------------------
        # Get trusted API keys
        # -------------------------------------------------

        trusted_api_keys = getattr(
            settings,
            "HUNAR_WEBHOOK_API_KEYS",
            [],
        )

        # -------------------------------------------------
        # Verify webhook signature
        # -------------------------------------------------

        is_valid = verify_hunar_webhook_signature(
            signature_header=signature,
            timestamp_header=timestamp,
            request_body=request_body,
            trusted_api_keys=trusted_api_keys,
        )

        if not is_valid:
            return HttpResponse(
                "Invalid webhook signature",
                status=401,
            )

        # -------------------------------------------------
        # Parse JSON
        # -------------------------------------------------

        try:
            payload = json.loads(
                request_body.decode("utf-8")
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return HttpResponse(
                "Invalid JSON",
                status=400,
            )

        # -------------------------------------------------
        # Get webhook information
        # -------------------------------------------------

        event_type = payload.get(
            "event_type"
        )

        call_id = payload.get(
            "call_id"
        )

        if not call_id:
            return HttpResponse(
                "Missing call_id",
                status=400,
            )

        # -------------------------------------------------
        # Find interview
        # -------------------------------------------------

        try:
            interview = Interview.objects.get(
                call_id=call_id
            )

        except Interview.DoesNotExist:
            return HttpResponse(
                "Interview not found",
                status=404,
            )

        # -------------------------------------------------
        # Store complete webhook payload
        # -------------------------------------------------

        interview.raw_payload = payload

        # -------------------------------------------------
        # Update call status
        # -------------------------------------------------

        if payload.get("status"):
            interview.status = payload[
                "status"
            ]

        # -------------------------------------------------
        # Update lifecycle status
        # -------------------------------------------------

        if payload.get("lifecycle_status"):
            interview.lifecycle_status = payload[
                "lifecycle_status"
            ]

        # -------------------------------------------------
        # Update answered-by information
        # -------------------------------------------------

        if payload.get("answered_by"):
            interview.answered_by = payload[
                "answered_by"
            ]

        # -------------------------------------------------
        # Update call-ended-by information
        # -------------------------------------------------

        if payload.get("call_ended_by"):
            interview.call_ended_by = payload[
                "call_ended_by"
            ]

        # -------------------------------------------------
        # Update duration
        # -------------------------------------------------

        if payload.get(
            "duration_seconds"
        ) is not None:
            interview.duration_seconds = payload[
                "duration_seconds"
            ]

        # -------------------------------------------------
        # Update recording URL
        # -------------------------------------------------

        if payload.get("recording_url"):
            interview.recording_url = payload[
                "recording_url"
            ]

        # -------------------------------------------------
        # Update AI result
        # -------------------------------------------------

        if payload.get("result") is not None:
            interview.result = payload[
                "result"
            ]

        # -------------------------------------------------
        # Save interview
        # -------------------------------------------------

        interview.save()

        # -------------------------------------------------
        # Return success
        # -------------------------------------------------

        return Response(
            {
                "ok": True,
                "event_type": event_type,
                "call_id": call_id,
                "interview_id": interview.id,
            },
            status=status.HTTP_200_OK,
        )
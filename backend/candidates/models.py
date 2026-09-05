from django.db import models

from hiring.models import Job


class Candidate(models.Model):
    """
    Candidate who applies for or is contacted about a job.
    """

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=20)

    # Resume content / extracted resume text.
    resume_text = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.job.title}"


class Interview(models.Model):
    """
    Stores a candidate's Hunar voice interview/call.
    """

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="interviews",
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="interviews",
    )

    # Hunar information
    hunar_agent_id = models.CharField(max_length=255)
    call_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    request_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=100,
        default="NOT_STARTED",
    )

    lifecycle_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    engagement_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    answered_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    call_ended_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    duration_seconds = models.FloatField(
        blank=True,
        null=True,
    )

    recording_url = models.URLField(
        blank=True,
        null=True,
    )

    # AI/Hunar result and raw response
    result = models.JSONField(
        default=dict,
        blank=True,
    )

    custom_data = models.JSONField(
        default=dict,
        blank=True,
    )

    raw_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.candidate.name} - {self.status}"
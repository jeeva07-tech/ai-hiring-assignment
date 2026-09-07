from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Candidate


DEMO_CANDIDATES = [
    {
        "name": "Arun Kumar",
        "title": "Python Developer",
        "location": "Chennai, Tamil Nadu",
        "skills": ["Python", "Django", "REST API", "PostgreSQL"],
        "experience": 2,
        "email": "arun.kumar@example.com",
        "mobile_number": "+919876543210",
    },
    {
        "name": "Priya Sharma",
        "title": "Backend Developer",
        "location": "Bangalore, Karnataka",
        "skills": ["Python", "Django", "PostgreSQL", "FastAPI"],
        "experience": 3,
        "email": "priya.sharma@example.com",
        "mobile_number": "+919876543211",
    },
    {
        "name": "Rahul Raj",
        "title": "Software Engineer",
        "location": "Chennai, Tamil Nadu",
        "skills": ["Python", "REST API", "SQL", "Machine Learning"],
        "experience": 2,
        "email": "rahul.raj@example.com",
        "mobile_number": "+919876543212",
    },
    {
        "name": "Divya Menon",
        "title": "AI/ML Engineer",
        "location": "Coimbatore, Tamil Nadu",
        "skills": ["Python", "Machine Learning", "Django", "PostgreSQL"],
        "experience": 2,
        "email": "divya.menon@example.com",
        "mobile_number": "+919876543213",
    },
]


class PeopleSearchView(APIView):
    """
    Search candidates and store the results in PostgreSQL.
    """

    def post(self, request):
        job_description = request.data.get("job_description", "").strip()

        if not job_description:
            return Response(
                {"error": "job_description is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # For now, this is our demo people-search provider.
        search_text = job_description.lower()

        results = []

        # Create a Job for this search.
        from hiring.models import Job

        job = Job.objects.create(
            title="AI Hiring Search",
            description=job_description,
        )

        for candidate_data in DEMO_CANDIDATES:
            candidate_text = " ".join(
                [
                    candidate_data["name"],
                    candidate_data["title"],
                    candidate_data["location"],
                    " ".join(candidate_data["skills"]),
                ]
            ).lower()

            keywords = [
                "python",
                "django",
                "postgresql",
                "rest",
                "api",
                "machine learning",
                "ai",
                "ml",
                "fastapi",
            ]

            matched_keywords = [
                keyword
                for keyword in keywords
                if keyword in search_text and keyword in candidate_text
            ]

            score = min(
                100,
                len(matched_keywords) * 15
                + min(candidate_data["experience"] * 5, 20),
            )

            # Save candidate in PostgreSQL.
            candidate = Candidate.objects.create(
                job=job,
                name=candidate_data["name"],
                email=candidate_data["email"],
                mobile_number=candidate_data["mobile_number"],
                resume_text=(
                    f"Title: {candidate_data['title']}\n"
                    f"Location: {candidate_data['location']}\n"
                    f"Skills: {', '.join(candidate_data['skills'])}\n"
                    f"Experience: {candidate_data['experience']} years"
                ),
            )

            results.append(
                {
                    "id": candidate.id,
                    "name": candidate.name,
                    "title": candidate_data["title"],
                    "location": candidate_data["location"],
                    "skills": candidate_data["skills"],
                    "experience": candidate_data["experience"],
                    "email": candidate.email,
                    "mobile_number": candidate.mobile_number,
                    "match_score": score,
                    "matched_keywords": matched_keywords,
                }
            )

        results.sort(
            key=lambda candidate: candidate["match_score"],
            reverse=True,
        )

        return Response(
            {
                "provider": "demo",
                "job_id": job.id,
                "job_description": job_description,
                "count": len(results),
                "candidates": results,
            },
            status=status.HTTP_200_OK,
        )
class CandidateListView(APIView):
    """
    Return saved candidates for the dashboard.
    """

    def get(self, request):
        candidates = Candidate.objects.select_related("job").order_by("-created_at")

        data = []

        for candidate in candidates:
            data.append(
                {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email,
                    "mobile_number": candidate.mobile_number,
                    "job_id": candidate.job.id,
                    "job_title": candidate.job.title,
                    "resume_text": candidate.resume_text,
                    "interviews": [
                        {
                            "id": interview.id,
                            "call_id": interview.call_id,
                            "status": interview.status,
                            "lifecycle_status": interview.lifecycle_status,
                            "engagement_status": interview.engagement_status,
                            "answered_by": interview.answered_by,
                            "duration_seconds": interview.duration_seconds,
                            "recording_url": interview.recording_url,
                            "result": interview.result,
                        }
                        for interview in candidate.interviews.all()
                    ],
                    "created_at": candidate.created_at,
                }
            )

        return Response(
            {
                "count": len(data),
                "candidates": data,
            },
            status=status.HTTP_200_OK,
        )
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class ApolloAPIError(Exception):
    """Raised when the Apollo API returns an error."""


class ApolloService:
    BASE_URL = "https://api.apollo.io/api/v1"

    def __init__(self):
        self.api_key = os.getenv("APOLLO_API_KEY")

        if not self.api_key:
            raise ApolloAPIError(
                "APOLLO_API_KEY is not configured."
            )

        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "accept": "application/json",
        }

    def search_people(
        self,
        job_titles=None,
        locations=None,
        keywords=None,
        page=1,
        per_page=10,
    ):
        payload = {
            "page": page,
            "per_page": per_page,
        }

        if job_titles:
            payload["person_titles[]"] = job_titles

        if locations:
            payload["person_locations[]"] = locations

        if keywords:
            payload["q_keywords"] = keywords

        response = requests.post(
            f"{self.BASE_URL}/mixed_people/api_search",
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise ApolloAPIError(
                f"Apollo API error {response.status_code}: "
                f"{response.text}"
            )

        return response.json()
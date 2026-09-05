import os

import requests
from dotenv import load_dotenv

load_dotenv()


class HunarAPIError(Exception):
    """Raised when the Hunar API returns an error."""


class HunarService:
    BASE_URL = os.getenv(
        "HUNAR_BASE_URL",
        "https://api.voice.hunar.ai/external/v1",
    ).rstrip("/")

    def __init__(self):
        self.api_key = os.getenv("HUNAR_API_KEY")

        if not self.api_key:
            raise HunarAPIError("HUNAR_API_KEY is not configured.")

        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def list_agents(self):
        response = requests.get(
            f"{self.BASE_URL}/agents/",
            headers=self.headers,
            timeout=30,
        )

        if response.status_code != 200:
            raise HunarAPIError(
                f"Hunar API error {response.status_code}: "
                f"{response.text}"
            )

        return response.json()

    def get_agent(self, agent_id):
        response = requests.get(
            f"{self.BASE_URL}/agents/{agent_id}/",
            headers=self.headers,
            timeout=30,
        )

        if response.status_code != 200:
            raise HunarAPIError(
                f"Hunar API error {response.status_code}: "
                f"{response.text}"
            )

        return response.json()

    def create_call(
        self,
        agent_id: str,
        callee_name: str,
        mobile_number: str,
        custom_data: dict | None = None,
        request_id: str | None = None,
        timezone: str = "Asia/Kolkata",
        callback_config: dict | None = None,
    ):
        payload = {
            "agent_id": agent_id,
            "callee_name": callee_name,
            "mobile_number": mobile_number,
            "timezone": timezone,
        }

        if custom_data:
            payload["custom_data"] = custom_data

        if request_id:
            payload["request_id"] = request_id

        if callback_config:
            payload["callback_config"] = callback_config

        response = requests.post(
            f"{self.BASE_URL}/calls/",
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise HunarAPIError(
                f"Hunar API error {response.status_code}: "
                f"{response.text}"
            )

        return response.json()

    def get_call(self, call_id: str):
        response = requests.get(
            f"{self.BASE_URL}/calls/{call_id}/",
            headers=self.headers,
            timeout=30,
        )

        if response.status_code != 200:
            raise HunarAPIError(
                f"Hunar API error {response.status_code}: "
                f"{response.text}"
            )

        return response.json()
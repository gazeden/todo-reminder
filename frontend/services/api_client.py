import logging
from typing import Any, Dict, Optional

import httpx
import streamlit as st

from config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """
    HTTP client for communicating with the backend.
    """

    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.token: Optional[str] = None
        self.timeout: int = 30.0

    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token

    def clear_token(self):
        self.token = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint (e.g., "/users/me")
            params: Query parameters

        Returns:
            Response JSON data
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}", headers=self._get_headers(), params=params
            )
            response.raise_for_status()
            return response.json()

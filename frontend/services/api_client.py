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

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login and get access token.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with access_token and user info
        """
        # OAuth2 form data
        form_data = {
            "username": email,  # OAuth2 spec uses 'username'
            "password": password,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{settings.API_BASE_URL}/auth/login",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

            # Set the token
            self.set_token(token_data["access_token"])

            # Get user info
            user_response = await client.get(
                f"{self.base_url}/users/me", headers=self._get_headers()
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            return {"access_token": token_data["access_token"], "user": user_data}


# Singleton instance
@st.cache_resource
def get_api_client() -> APIClient:
    """
    Get or create API client singleton.
    Uses Streamlit's cache_resource to maintain a single instance.
    """
    client = APIClient()

    # If there's a token in session state, set it
    if "access_token" in st.session_state:
        client.set_token(st.session_state.access_token)

    return client

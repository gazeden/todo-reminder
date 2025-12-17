import logging
from typing import Any, Dict, List, Optional

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

    async def get(self, endpoint: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
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

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data

        Returns:
            Response JSON data
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                data=data,
                json=json,
            )
            response.raise_for_status()
            return response.json()

    async def put(self, endpoint: str, json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint
            json: JSON data

        Returns:
            Response JSON data
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(
                f"{self.base_url}{endpoint}", headers=self._get_headers(), json=json
            )
            response.raise_for_status()
            return response.json()

    async def delete(self, endpoint: str) -> None:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}{endpoint}", headers=self._get_headers()
            )
            response.raise_for_status()

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

    async def register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            user_data: User registration data

        Returns:
            Created user data
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/users/",
                json=user_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    # User endpoints
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user."""
        return await self.get("/users/me")

    async def update_user(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        return await self.put(f"/users/{user_id}", json=data)

    async def get_tasks(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        """Get list of tasks."""
        params = {"skip": skip, "limit": limit, "include_inactive": include_inactive}
        if status:
            params["status"] = status
        return await self.get("/tasks", params=params)

    async def get_task(self, task_id: int) -> Dict[str, Any]:
        """Get single task by ID."""
        return await self.get(f"/tasks/{task_id}")

    async def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        return await self.post("/tasks", json=data)

    async def update_task(self, task_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task."""
        return await self.put(f"/tasks/{task_id}", json=data)

    async def delete_task(self, task_id: int) -> None:
        """Delete a task."""
        await self.delete(f"/tasks/{task_id}")

    async def complete_task(
        self, task_id: int, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark task as completed."""
        data = {"notes": notes} if notes else {}
        return await self.post(f"/tasks/{task_id}/complete", json=data)

    async def get_due_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are due."""
        return await self.get("/tasks/due")

    async def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks."""
        return await self.get("/tasks/overdue")

    async def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        return await self.get("/tasks/stats")

    async def get_task_completions(
        self, task_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get completion history for a task."""
        return await self.get(f"/tasks/{task_id}/completions", params={"limit": limit})


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

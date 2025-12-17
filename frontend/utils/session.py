from datetime import datetime, timedelta
from typing import Any

import streamlit as st


def init_session_state():
    """
    Initialize session state variables.
    Should be called at the start of the app.
    """
    # Authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None

    if "access_token" not in st.session_state:
        st.session_state.access_token = None

    if "last_activity" not in st.session_state:
        st.session_state.last_activity = datetime.now()

    # UI state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    if "show_sidebar" not in st.session_state:
        st.session_state.show_sidebar = True

    # Data cache
    if "items_cache" not in st.session_state:
        st.session_state.items_cache = None

    if "cache_timestamp" not in st.session_state:
        st.session_state.cache_timestamp = None


def check_authentication() -> bool:
    """
    Check if user is authenticated and session is still valid.

    Returns:
        True if authenticated and session valid, False otherwise
    """
    from config import settings

    if not st.session_state.get("authenticated", False):
        return False

    # Check session timeout
    if st.session_state.get("last_activity"):
        elapsed = datetime.now() - st.session_state.last_activity
        if elapsed > timedelta(minutes=settings.SESSION_TIMEOUT):
            logout()
            st.warning("Session expired. Please login again.")
            return False

    # Update last activity
    st.session_state.last_activity = datetime.now()
    return True


def require_authentication(redirect_to_login: bool = True):
    """
    Decorator/function to require authentication for a page.

    Args:
        redirect_to_login: Whether to redirect to login page if not authenticated
    """
    if not check_authentication():
        if redirect_to_login:
            st.warning("Please login to access this page")
            st.switch_page("🏠_Home.py")
        st.stop()


def logout():
    """
    Logout current user and clear session state.
    """
    from services.api_client import get_api_client

    # Clear API client token
    api_client = get_api_client()
    api_client.clear_token()

    # Clear session state
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.items_cache = None
    st.session_state.cache_timestamp = None

    st.success("Logged out successfully")


def update_cache(key: str, value: Any, ttl_minutes: int = 5):
    """
    Update cached data with TTL.

    Args:
        key: Cache key
        value: Value to cache
        ttl_minutes: Time to live in minutes
    """
    cache_key = f"{key}_cache"
    timestamp_key = f"{key}_cache_timestamp"

    st.session_state[cache_key] = value
    st.session_state[timestamp_key] = datetime.now()


def get_cache(key: str, ttl_minutes: int = 5) -> Any:
    """
    Get cached data if still valid.

    Args:
        key: Cache key
        ttl_minutes: Time to live in minutes

    Returns:
        Cached value or None if expired/not found
    """
    cache_key = f"{key}_cache"
    timestamp_key = f"{key}_cache_timestamp"

    if cache_key not in st.session_state or timestamp_key not in st.session_state:
        return None

    timestamp = st.session_state[timestamp_key]
    if datetime.now() - timestamp > timedelta(minutes=ttl_minutes):
        return None

    return st.session_state[cache_key]


def clear_cache(key: str = None):
    """
    Clear cached data.

    Args:
        key: Specific cache key to clear, or None to clear all
    """
    if key:
        cache_key = f"{key}_cache"
        timestamp_key = f"{key}_cache_timestamp"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        if timestamp_key in st.session_state:
            del st.session_state[timestamp_key]
    else:
        # Clear all cache entries
        keys_to_delete = [
            k
            for k in st.session_state.keys()
            if k.endswith("_cache") or k.endswith("_cache_timestamp")
        ]
        for k in keys_to_delete:
            del st.session_state[k]

from datetime import datetime
from typing import Any, Optional

import streamlit as st


def format_date(date_str: str, format: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format ISO date string to readable format.

    Args:
        date_str: ISO format date string
        format: Output format string

    Returns:
        Formatted date string
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime(format)
    except Exception:
        return date_str


def format_relative_time(date_str: str) -> str:
    """
    Format date as relative time (e.g., "2 hours ago").

    Args:
        date_str: ISO format date string

    Returns:
        Relative time string
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return format_date(date_str, "%Y-%m-%d")
    except Exception:
        return date_str


def truncate_text(
    text: Optional[str], max_length: int = 100, suffix: str = "..."
) -> str:
    """
    Truncate text to max length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def display_success(message: str):
    """Display success message with icon."""
    st.success(f"✅ {message}")


def display_error(message: str):
    """Display error message with icon."""
    st.error(f"❌ {message}")


def display_warning(message: str):
    """Display warning message with icon."""
    st.warning(f"⚠️ {message}")


def display_info(message: str):
    """Display info message with icon."""
    st.info(f"ℹ️ {message}")


def format_number(number: Any, decimals: int = 0) -> str:
    """
    Format number with thousand separators.

    Args:
        number: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted number string
    """
    try:
        if decimals > 0:
            return f"{float(number):,.{decimals}f}"
        else:
            return f"{int(number):,}"
    except Exception:
        return str(number)


def create_badge(text: str, color: str = "blue") -> str:
    """
    Create a colored badge in markdown.

    Args:
        text: Badge text
        color: Badge color (blue, green, red, orange, gray)

    Returns:
        HTML string for badge
    """
    colors = {
        "blue": "#1f77b4",
        "green": "#2ca02c",
        "red": "#d62728",
        "orange": "#ff7f0e",
        "gray": "#7f7f7f",
    }

    bg_color = colors.get(color, colors["blue"])

    return f"""
    <span style="
        background-color: {bg_color};
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
    ">{text}</span>
    """

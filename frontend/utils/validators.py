import re
from typing import Optional


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, None


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.

    Args:
        password: Password string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if len(password) > 100:
        return False, "Password is too long"

    # Check for at least one letter and one number
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format.

    Args:
        username: Username string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username is too long"

    # Only alphanumeric and underscore allowed
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"

    return True, None


def validate_required(value: any, field_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a field is not empty.

    Args:
        value: Value to check
        field_name: Name of the field for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"{field_name} is required"

    return True, None

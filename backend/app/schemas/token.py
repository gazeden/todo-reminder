from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema for JWT."""

    sub: Optional[int] = None  # User ID
    exp: Optional[int] = None  # Expiration time

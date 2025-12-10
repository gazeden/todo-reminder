from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .task import Task


class User(SQLModel, table=True):
    """
    User database model.
    """

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=50)
    full_name: str = Field(default=None, max_length=100)
    hashed_password: str = Field(max_length=255)

    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    tasks: List["Task"] = Relationship(back_populates="owner")

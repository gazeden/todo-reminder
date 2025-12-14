from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, String
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class RecurrenceUnit(StrEnum):
    """Time unit for recurrence interval."""

    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


class TaskStatus(StrEnum):
    """Task status."""

    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    SNOOZED = "snoozed"


class Task(SQLModel, table=True):
    """
    Task/Todo database model with flexible recurrence support.
    """

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)

    # Recurrence Configuration
    is_recurring: bool = Field(default=False)

    # Interval-based recurrence (every N days/weeks/months)
    recurrence_interval: Optional[int] = Field(default=None)  # The number (N)
    recurrent_unit: Optional[RecurrenceUnit] = Field(default=None)  # days/weeks/months

    # Specific days of week (for weekly patterns like "every Tuesday and Thursday")
    # Stores array of day numbers: 0=Monday, 1=Tuesday, ..., 6=Sunday
    specific_days_of_week: Optional[List[int]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )

    # Specific days of month (for monthly patterns like "on the 1st and 15th")
    specific_days_of_month: Optional[List[int]] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )

    # Status and completion
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    completed_at: Optional[datetime] = Field(default=None)

    # Next occurrence tracking
    next_due_date: Optional[datetime] = Field(default=None, index=True)
    last_completed_date: Optional[datetime] = Field(default=None)

    # Reminder settings
    reminder_enabled: bool = Field(default=True)
    reminder_time: Optional[str] = Field(default=None)  # Time in HH:MM format
    reminder_minutes_before: Optional[int] = Field(default=None)  # Minutes before due

    # Metadata
    is_active: bool = Field(default=True, index=True)
    owner_id: int = Field(foreign_key="users.id", index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    ownwer: Optional["User"] = Relationship(back_populates="tasks")
    completions: List["TaskCompletion"] = Relationship(back_populates="task")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "title": "Water plants",
                    "description": "Water all indoor plants",
                    "is_recurring": True,
                    "recurrence_interval": 3,
                    "recurrence_unit": "days",
                    "reminder_enabled": True,
                    "reminder_time": "09:00",
                },
                {
                    "title": "Team meeting",
                    "description": "Weekly team sync",
                    "is_recurring": True,
                    "specific_days_of_week": [1, 3],  # Tuesday and Thursday
                    "reminder_enabled": True,
                    "reminder_time": "10:00",
                },
                {
                    "title": "Pay rent",
                    "description": "Monthly rent payment",
                    "is_recurring": True,
                    "recurrence_interval": 1,
                    "recurrence_unit": "months",
                    "specific_days_of_month": [1],  # 1st of month
                    "reminder_enabled": True,
                    "reminder_time": "09:00",
                },
            ]
        }


class TaskCompletion(SQLModel, table=True):
    """
    Track task completion history.
    """

    __tablename__ = "task_completions"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    notes: Optional[str] = Field(default=None, max_chars=500)

    # Relationships
    task: Optional[Task] = Relationship(back_populates="completions")

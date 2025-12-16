from datetime import datetime
from typing import List, Optional

from app.models.task import RecurrenceUnit, TaskStatus
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    # Recurrence settings
    is_recurring: bool = False
    recurrence_interval: Optional[int] = Field(None, ge=1, le=999)
    recurrence_unit: Optional[RecurrenceUnit] = None
    specific_days_of_week: Optional[List[int]] = Field(None, max_length=7)
    specific_days_of_month: Optional[List[int]] = Field(None, max_length=31)

    # Reminder settings
    reminder_enabled: bool = True
    reminder_time: Optional[str] = Field(
        None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    )
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=1440)

    is_active: bool = True

    @field_validator("specific_days_of_week")
    @classmethod
    def validate_days_of_week(cls, v: Optional[List[int]]):
        """Validate days of week are in range 0-6."""
        if v is not None:
            for day in v:
                if not (0 <= day <= 6):
                    raise ValueError(
                        "Days of week must be between 0 (Monday) and 6 (Sunday)"
                    )
            if len(v) != len(set(v)):
                raise ValueError("Duplicate days of week not allowed")
        return v

    @field_validator("specific_days_of_month")
    @classmethod
    def validate_days_of_month(cls, v: Optional[List[int]]):
        """Validate days of month are in range 1-31."""
        if v is not None:
            for day in v:
                if not (1 <= day <= 31):
                    raise ValueError("Days of month must be between 1 and 31")
            if len(v) != len(set(v)):
                raise ValueError("Duplicate days of month not allowed")
        return v

    @field_validator("recurrence_unit")
    @classmethod
    def validate_recurrence(cls, v: Optional[RecurrenceUnit], info):
        """Validate recurrence settings."""
        is_recurring = info.data.get("is_recurring", False)
        recurrence_interval = info.data.get("recurrence_interval")
        specific_days_of_week = info.data.get("specific_days_of_week")
        specific_days_of_month = info.data.get("specific_days_of_month")

        if is_recurring:
            # Must have either interval+unit and/or specific days
            has_interval = recurrence_interval is not None and v is not None
            has_specific_days = (
                specific_days_of_week is not None
                and len(specific_days_of_week) > 0
                or specific_days_of_month is not None
                and len(specific_days_of_month) > 0
            )

            if not has_interval and not has_specific_days:
                raise ValueError(
                    "Recurring tasks must specify either interval+unit or specific days"
                )

        return v


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    is_recurring: Optional[bool] = None
    recurrence_interval: Optional[int] = Field(None, ge=1, le=999)
    recurrence_unit: Optional[RecurrenceUnit] = None
    specific_days_of_week: Optional[List[int]] = None
    specific_days_of_month: Optional[List[int]] = None
    status: Optional[TaskStatus] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = Field(
        None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    )
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=1440)
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: int
    owner_id: int
    status: TaskStatus
    completed_at: Optional[datetime]
    next_due_date: Optional[datetime]
    last_completed_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Schema for paginated task list."""

    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskCompleteRequest(BaseModel):
    """Schema for completing a task."""

    notes: Optional[str] = Field(None, max_length=500)


class TaskCompletionResponse(BaseModel):
    """Schema for task completion response."""

    id: int
    task_id: int
    completed_at: datetime
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TaskStatsResponse(BaseModel):
    """Schema for task statistics."""

    total_tasks: int
    pending_tasks: int
    completed_today: int
    overdue_tasks: int
    completion_rate: float
    streak_days: int

"""
Pydantic models for Kafka events.
These automatically serialize to dicts matching Avro schemas.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.task import RecurrenceUnit, Task
from app.models.user import User
from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    """Metadata included in all events."""

    producer: str = "todo-reminder-backend"
    version: str = "1.0.0"


class RecurrenceConfig(BaseModel):
    """Task recurrence configuration."""

    interval: Optional[int] = None
    unit: Optional[RecurrenceUnit] = None
    specific_days_of_week: Optional[List[int]] = None
    specific_days_of_month: Optional[List[int]] = None


# User Events
class UserCreatedEvent(BaseModel):
    """Event published when a user is created."""

    user_id: int
    email: str
    username: str
    timestamp: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_user(cls, user: User):
        """Create event from User model."""
        return cls(
            user_id=user.id,
            email=user.email,
            username=user.username,
            timestamp=user.created_at.isoformat(),
        )


class UserUpdatedEvent(BaseModel):
    """Event published when a user is updated."""

    user_id: int
    email: str
    timestamp: str
    changed_fields: List[str]
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_user(cls, user: User, changed_fields: List[str]):
        """Create event from User model."""
        return cls(
            user_id=user.id,
            email=user.email,
            timestamp=user.updated_at.isoformat(),
            changed_fields=changed_fields,
        )


class UserLoginEvent(BaseModel):
    """Event published when a user logs in."""

    user_id: int
    email: str
    timestamp: str
    ip_address: Optional[str] = None
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_user(cls, user: User, ip_address: Optional[str] = None):
        """Create event from User model."""
        return cls(
            user_id=user.id,
            email=user.email,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ip_address=ip_address,
        )


# Task Events
class TaskCreatedEvent(BaseModel):
    """Event published when a task is created."""

    task_id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    is_recurring: bool
    recurrence_config: Optional[RecurrenceConfig] = None
    next_due_date: Optional[str] = None
    reminder_enabled: bool
    reminder_time: Optional[str] = None
    timestamp: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_task(cls, task: Task):
        """Create event from Task model."""
        recurrence_config = None
        if task.is_recurring:
            recurrence_config = RecurrenceConfig(
                interval=task.recurrence_interval,
                unit=task.recurrence_unit,
                specific_days_of_week=task.specific_days_of_week,
                specific_days_of_month=task.specific_days_of_month,
            )

        return cls(
            task_id=task.id,
            owner_id=task.owner_id,
            title=task.title,
            description=task.description,
            is_recurring=task.is_recurring,
            recurrence_config=recurrence_config,
            next_due_date=task.next_due_date.isoformat()
            if task.next_due_date
            else None,
            reminder_enabled=task.reminder_enabled,
            reminder_time=task.reminder_time,
            timestamp=task.created_at.isoformat(),
        )


class TaskUpdatedEvent(BaseModel):
    """Event published when a task is updated."""

    task_id: int
    owner_id: int
    title: str
    status: str
    timestamp: str
    changed_fields: List[str]
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_task(cls, task: Task, changed_fields: List[str]):
        """Create event from Task model."""
        return cls(
            task_id=task.id,
            owner_id=task.owner_id,
            title=task.title,
            status=task.status,
            timestamp=task.updated_at.isoformat(),
            changed_fields=changed_fields,
        )


class TaskCompletedEvent(BaseModel):
    """Event published when a task is completed."""

    task_id: int
    owner_id: int
    title: str
    completed_at: str
    next_due_date: Optional[str] = None
    is_recurring: bool
    notes: Optional[str] = None
    timestamp: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_task(cls, task: Task, notes: Optional[str] = None):
        """Create event from Task model."""
        return cls(
            task_id=task.id,
            owner_id=task.owner_id,
            title=task.title,
            completed_at=task.completed_at.isoformat()
            if task.completed_at
            else datetime.now(timezone.utc).isoformat(),
            next_due_date=task.next_due_date.isoformat()
            if task.next_due_date
            else None,
            is_recurring=task.is_recurring,
            notes=notes,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class TaskDeletedEvent(BaseModel):
    """Event published when a task is deleted."""

    task_id: int
    owner_id: int
    title: str
    timestamp: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_task(cls, task: Task):
        """Create event from Task model."""
        return cls(
            task_id=task.id,
            owner_id=task.owner_id,
            title=task.title,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


class TaskDueReminderEvent(BaseModel):
    """Event published for task due reminders."""

    task_id: int
    owner_id: int
    title: str
    due_date: str
    reminder_type: str  # "due" or "advance"
    minutes_before: Optional[int] = None
    timestamp: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @classmethod
    def from_task(
        cls,
        task: Task,
        reminder_type: str = "due",
        minutes_before: Optional[int] = None,
    ):
        """Create event from Task model."""
        return cls(
            task_id=task.id,
            owner_id=task.owner_id,
            title=task.title,
            due_date=task.next_due_date.isoformat()
            if task.next_due_date
            else datetime.now(timezone.utc).isoformat(),
            reminder_type=reminder_type,
            minutes_before=minutes_before,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

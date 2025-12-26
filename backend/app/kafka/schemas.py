"""
Avro schemas for Kafka events.
All events should follow these schemas for consistency and validation.
"""

# User event schemas
USER_CREATED_SCHEMA = {
    "type": "record",
    "name": "UserCreated",
    "namespace": "com.todo_reminder.events.user",
    "fields": [
        {"name": "user_id", "type": "int"},
        {"name": "email", "type": "string"},
        {"name": "username", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {
            "name": "metadata",
            "type": {
                "type": "record",
                "name": "EventMetadata",
                "fields": [
                    {"name": "producer", "type": "string"},
                    {"name": "version", "type": "string", "default": "1.0.0"},
                ],
            },
        },
    ],
}

USER_UPDATED_SCHEMA = {
    "type": "record",
    "name": "UserUpdated",
    "namespace": "com.todo_reminder.events.user",
    "fields": [
        {"name": "user_id", "type": "int"},
        {"name": "email", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "changed_fields", "type": {"type": "array", "items": "string"}},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

USER_LOGIN_SCHEMA = {
    "type": "record",
    "name": "UserLogin",
    "namespace": "com.todo_reminder.events.user",
    "fields": [
        {"name": "user_id", "type": "int"},
        {"name": "email", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "ip_address", "type": ["null", "string"], "default": None},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

# Task event schemas
TASK_CREATED_SCHEMA = {
    "type": "record",
    "name": "TaskCreated",
    "namespace": "com.todo_reminder.events.task",
    "fields": [
        {"name": "task_id", "type": "int"},
        {"name": "owner_id", "type": "int"},
        {"name": "title", "type": "string"},
        {"name": "description", "type": ["null", "string"], "default": None},
        {"name": "is_recurring", "type": "boolean"},
        {
            "name": "recurrence_config",
            "type": [
                "null",
                {
                    "type": "record",
                    "name": "RecurrenceConfig",
                    "fields": [
                        {"name": "interval", "type": ["null", "int"], "default": None},
                        {"name": "unit", "type": ["null", "string"], "default": None},
                        {
                            "name": "specific_days_of_week",
                            "type": ["null", {"type": "array", "items": "int"}],
                            "default": None,
                        },
                        {
                            "name": "specific_days_of_month",
                            "type": ["null", {"type": "array", "items": "int"}],
                            "default": None,
                        },
                    ],
                },
            ],
            "default": None,
        },
        {"name": "next_due_date", "type": ["null", "string"], "default": None},
        {"name": "reminder_enabled", "type": "boolean"},
        {"name": "reminder_time", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": "string"},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

TASK_UPDATED_SCHEMA = {
    "type": "record",
    "name": "TaskUpdated",
    "namespace": "com.todo_reminder.events.task",
    "fields": [
        {"name": "task_id", "type": "int"},
        {"name": "owner_id", "type": "int"},
        {"name": "title", "type": "string"},
        {"name": "status", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "changed_fields", "type": {"type": "array", "items": "string"}},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

TASK_COMPLETED_SCHEMA = {
    "type": "record",
    "name": "TaskCompleted",
    "namespace": "com.todo_reminder.events.task",
    "fields": [
        {"name": "task_id", "type": "int"},
        {"name": "owner_id", "type": "int"},
        {"name": "title", "type": "string"},
        {"name": "completed_at", "type": "string"},
        {"name": "next_due_date", "type": ["null", "string"], "default": None},
        {"name": "is_recurring", "type": "boolean"},
        {"name": "notes", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": "string"},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

TASK_DELETED_SCHEMA = {
    "type": "record",
    "name": "TaskDeleted",
    "namespace": "com.todo_reminder.events.task",
    "fields": [
        {"name": "task_id", "type": "int"},
        {"name": "owner_id", "type": "int"},
        {"name": "title", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

TASK_DUE_REMINDER_SCHEMA = {
    "type": "record",
    "name": "TaskDueReminder",
    "namespace": "com.todo_reminder.events.task",
    "fields": [
        {"name": "task_id", "type": "int"},
        {"name": "owner_id", "type": "int"},
        {"name": "title", "type": "string"},
        {"name": "due_date", "type": "string"},
        {"name": "reminder_type", "type": "string"},  # "due" or "advance"
        {"name": "minutes_before", "type": ["null", "int"], "default": None},
        {"name": "timestamp", "type": "string"},
        {"name": "metadata", "type": "EventMetadata"},
    ],
}

# Schema registry for topic -> schema mapping
TOPIC_SCHEMAS = {
    "user.created": USER_CREATED_SCHEMA,
    "user.updated": USER_UPDATED_SCHEMA,
    "user.login": USER_LOGIN_SCHEMA,
    "task.created": TASK_CREATED_SCHEMA,
    "task.updated": TASK_UPDATED_SCHEMA,
    "task.completed": TASK_COMPLETED_SCHEMA,
    "task.deleted": TASK_DELETED_SCHEMA,
    "task.due_reminder": TASK_DUE_REMINDER_SCHEMA,
}

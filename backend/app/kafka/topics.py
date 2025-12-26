from enum import StrEnum

from app.config import settings


class KafkaTopics(StrEnum):
    """
    Centralized Kafka topic names.
    """

    # User topics
    USER_CREATED = f"{settings.KAFKA_TOPIC_PREFIX}.user.created"
    USER_UPDATED = f"{settings.KAFKA_TOPIC_PREFIX}.user.updated"
    USER_DELETED = f"{settings.KAFKA_TOPIC_PREFIX}.user.deleted"
    USER_LOGIN = f"{settings.KAFKA_TOPIC_PREFIX}.user.login"

    # Task topics
    TASK_CREATED = f"{settings.KAFKA_TOPIC_PREFIX}.task.created"
    TASK_UPDATED = f"{settings.KAFKA_TOPIC_PREFIX}.task.updated"
    TASK_DELETED = f"{settings.KAFKA_TOPIC_PREFIX}.task.deleted"
    TASK_COMPLETED = f"{settings.KAFKA_TOPIC_PREFIX}.task.completed"
    TASK_DUE_REMINDER = f"{settings.KAFKA_TOPIC_PREFIX}.task.due_reminder"


# Topic configurations
TOPIC_CONFIGS = {
    KafkaTopics.USER_CREATED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,  # 7 days
    },
    KafkaTopics.USER_UPDATED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,
    },
    KafkaTopics.USER_DELETED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 2592000000,  # 30 days (keep for audit)
    },
    KafkaTopics.USER_LOGIN: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,
    },
    KafkaTopics.TASK_CREATED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,
    },
    KafkaTopics.TASK_UPDATED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,
    },
    KafkaTopics.TASK_DELETED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 2592000000,
    },
    KafkaTopics.TASK_COMPLETED: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 2592000000,  # 30 days for analytics
    },
    KafkaTopics.TASK_DUE_REMINDER: {
        "num_partitions": 3,
        "replication_factor": 1,
        "retention_ms": 86400000,  # 1 day
    },
}

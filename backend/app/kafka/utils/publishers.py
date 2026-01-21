"""
Helper functions for publishing events.
"""

import logging
from typing import Optional

from app.config import settings
from pydantic import BaseModel

if settings.USE_SCHEMA_REGISTRY:
    from app.kafka.producers.schema_registry_producer import (
        schema_registry_producer as producer,
    )
else:
    from app.kafka.producers.producer import kafka_producer as producer


logger = logging.getLogger(__name__)


def publish_event(topic: str, event: BaseModel, key: Optional[str] = None) -> None:
    """
    Publish an event to Kafka.

    Args:
        topic: Topic name (without prefix)
        event: Pydantic event model
        key: Partition key (usually entity ID)
    """
    try:
        if settings.USE_SCHEMA_REGISTRY:
            # Synchronous with schema validation
            producer.send_event(topic, event, key=key)
        else:
            # Async without schema validation
            import asyncio

            asyncio.create_task(producer.send_event(topic, event.model_dump(), key=key))

        logger.info("Published %s to %s", event.__class__.__name__, topic)

    except Exception as e:
        logger.error(f"Failed to publish event to {topic}: {e}")
        # Don't raise - event publishing failures shouldn't fail API requests

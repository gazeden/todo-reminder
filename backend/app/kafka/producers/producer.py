import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from app.config import settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """
    Kafka producer service for publishing events.
    """

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self._started: bool = False

    async def start(self) -> None:
        """
        Start the Kafka producer.
        """
        if self._started:
            logger.warning("Kafka producer already started")
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=self._serialize_value,
                key_serializer=self._serialize_key,
                acks=settings.KAFKA_ACKS,
                enable_idempotence=settings.KAFKA_ENABLE_IDEMPOTENCE,
                max_in_flight_requests_per_connection=5,
                retries=3,
                compression_type="gzip",
            )
            await self.producer.start()
            self._started = True
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop the Kafka producer.
        """
        if not self._started:
            logger.warning("Kafka producer not started")
            return

        try:
            if self.producer:
                await self.producer.stop()
                self._started = False
                logger.info("Kafka producer stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}")
            raise

    @staticmethod
    def _serialize_value(value: Dict[str, Any]) -> bytes:
        """
        Serialize event value to JSON bytes.
        """
        return json.dumps(value, default=str).encode("utf-8")

    @staticmethod
    def _serialize_key(key: Optional[str]) -> Optional[bytes]:
        """
        Serialize event key to bytes.
        """
        if key is None:
            return None
        return key.encode("utf-8")

    async def send_event(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Send an event to a Kafka topic.

        Args:
            topic: Topic name (without prefix, will be added automatically)
            event: Event data dictionary
            key: Partition key (typically entity ID)
            headers: Optional event headers
        """
        if not self._started or not self.producer:
            logger.error("Kafka producer not started")
            raise RuntimeError("Kafka producer not started")

        # Add prefix to topic
        full_topic = f"{settings.KAFKA_TOPIC_PREFIX}.{topic}"

        # Add metadata to event
        event_with_metadata = {
            **event,
            "_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "producer": "todo-reminder-backend",
                "topic": full_topic,
            },
        }

        # Prepare headers
        kafka_headers = []
        if headers:
            kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

        try:
            # Send event
            future = await self.producer.send(
                topic=full_topic,
                value=event_with_metadata,
                key=key,
                headers=kafka_headers,
            )

            # Wait for acknowledgment
            record_metadata = await future

            logger.info(
                f"Event sent to {full_topic} "
                f"(partition: {record_metadata.partition}, "
                f"offset: {record_metadata.offset})"
            )

        except KafkaError as e:
            logger.error(f"Failed to send event to {full_topic}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending event to {full_topic}: {e}")
            raise

    async def send_batch(
        self, topic: str, events: list[Dict[str, Any]], keys: Optional[list[str]] = None
    ) -> None:
        """
        Send multiple events in batch.

        Args:
            topic: Topic name
            events: List of event dictionaries
            keys: Optional list of keys (same length as events)
        """
        if not self._started or not self.producer:
            raise RuntimeError("Kafka producer not started")

        if keys and len(keys) != len(events):
            raise ValueError("Keys list must have same length as events list")

        full_topic = f"{settings.KAFKA_TOPIC_PREFIX}.{topic}"

        try:
            batch = self.producer.create_batch()

            for i, event in enumerate(events):
                key = keys[i] if keys else None
                event_with_metadata = {
                    **event,
                    "_metadata": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "producer": "todo-reminder-backend",
                        "topic": full_topic,
                    },
                }

                metadata = batch.append(
                    key=self._serialize_key(key),
                    value=self._serialize_value(event_with_metadata),
                    timestamp=None,
                    headers=None,
                )

                if metadata is None:
                    # Batch is full, send it
                    await self.producer.send_batch(batch, full_topic)
                    batch = self.producer.create_batch()

                    # Retry appending current event
                    batch.append(
                        key=self._serialize_key(key),
                        value=self._serialize_value(event_with_metadata),
                        timestamp=None,
                        headers=None,
                    )

            # Send remaining events
            if not batch.is_empty():
                await self.producer.send_batch(batch, full_topic)

            logger.info(f"Batch of {len(events)} events sent to {full_topic}")

        except Exception as e:
            logger.error(f"Failed to send batch to {full_topic}: {e}")
            raise


# Singleton instance
kafka_producer = KafkaProducerService()

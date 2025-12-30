import logging
from typing import Any, Dict, Optional, Union

from app.config import settings
from app.kafka.schemas import TOPIC_SCHEMAS
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SchemaRegistryProducerService:
    """
    Kafka producer with Schema Registry for enforcing event schemas.
    """

    def __init__(self):
        self.producer: Optional[SerializingProducer] = None
        self.schema_registry_client: Optional[SchemaRegistryClient] = None
        self.serializers: Dict[str, AvroSerializer] = {}
        self._started = False

    def start(self) -> None:
        """Initialize the producer and schema registry client."""
        if self._started:
            logger.warning("Schema Registry producer already started")
            return

        try:
            schema_registry_conf = {"url": settings.SCHEMA_REGISTRY_URL}

            if hasattr(settings, "SCHEMA_REGISTRY_API_KEY"):
                schema_registry_conf["basic.auth.user.info"] = (
                    f"{settings.SCHEMA_REGISTRY_API_KEY}:{settings.SCHEMA_REGISTRY_API_SECRET}"
                )

            self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
            self._register_schemas()

            producer_conf = {
                "boostrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "key.serializer": StringSerializer("utf_8"),
                "acks": settings.KAFKA_ACKS,
                "enable.idempotence": settings.KAFKA_ENABLE_IDEMPOTENCE,
            }

            self.producer = SerializingProducer(producer_conf)
            self._started = True

            logger.info("Schema Registry producer started successfully")

        except Exception as e:
            logger.error(f"Failed to start Schema Registry producer: {e}")
            raise

    def stop(self) -> None:
        """Stop the producer and flush pending messages."""
        if not self._started:
            return

        try:
            if self.producer:
                self.producer.flush()
                self._started = False
                logger.info("Schema Registry producer stopped")
        except Exception as e:
            logger.error(f"Error stopping producer: {e}")
            raise

    def _register_schemas(self) -> None:
        """Register all schemas with the Schema Registry and create serializers."""
        for topic_suffix, schema in TOPIC_SCHEMAS.items():
            full_topic = f"{settings.KAFKA_TOPIC_PREFIX}.{topic_suffix}"
            subject = f"{full_topic}-value"

            try:
                schema_id = self.schema_registry_client.register_schema(
                    subject_name=subject,
                    schema={"type": "record", **schema}
                    if schema.get("type") == "record"
                    else schema,
                )

                logger.info("Registered schema for %s with ID: %s", subject, schema_id)

                self.serializers[topic_suffix] = AvroSerializer(
                    self.schema_registry_client,
                    schema,
                    lambda obj, ctx: obj,  # No transformation
                )

            except Exception as e:
                logger.error(f"Failed to register schema for {subject}: {e}")
                raise

    def send_event(
        self,
        topic: str,
        event: Union[BaseModel, Dict[str, Any]],  # Accepts Pydantic or dict
        key: Optional[str] = None,
        callback: Optional[callable] = None,
    ) -> None:
        """
        Send an event to Kafka with schema validation.

        Args:
            topic: Topic name (without prefix)
            event: Event data (Pydantic model or dict)
            key: Partition key
            callback: Optional delivery report callback
        """
        if not self._started or not self.producer:
            raise RuntimeError("Producer not started")

        serializer = self.serializers.get(topic)
        if not serializer:
            raise ValueError(f"No schema registered for topic: {topic}")

        # Convert Pydantic model to dict if needed
        if isinstance(event, BaseModel):
            event_dict = event.model_dump(mode="json")
        else:
            event_dict = event

        full_topic = f"{settings.KAFKA_TOPIC_PREFIX}.{topic}"

        try:
            self.producer.produce(
                topic=full_topic,
                key=key,
                value=event_dict,
                value_serializer=serializer.serialize,
                on_delivery=callback or self._delivery_report,
            )

            self.producer.poll(0)

            logger.info("Event sent to %s (key: %s)", full_topic, key)

        except Exception as e:
            logger.error(f"Failed to send event to {full_topic}: {e}")
            raise

    def flush(self, timeout: float = 10.0) -> None:
        """Flush pending messages."""
        if self.producer:
            remaining = self.producer.flush(timeout)
            if remaining > 0:
                logger.warning("%d messages were not delivered", remaining)

    @staticmethod
    def delivery_report(err, msg):
        """Default delivery report callback."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[partition {msg.partition()}] at offset {msg.offset()}"
            )


schema_registry_producer = SchemaRegistryProducerService()

import copy
import json
import logging
from typing import Any, Dict, List, Optional, Union

import fastavro
from app.config import settings
from app.kafka.schemas import TOPIC_SCHEMAS
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry.common.schema_registry_client import Schema
from confluent_kafka.serialization import MessageField, SerializationContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SchemaRegistryProducerService:
    """
    Kafka producer with Schema Registry for enforcing event schemas.
    """

    def __init__(self):
        self.producer: Optional[Producer] = None
        self.schema_registry_client: Optional[SchemaRegistryClient] = None
        self.parsed_schemas: Dict[str, Any] = {}  # Cache parsed base schemas
        self.serializers: Dict[str, AvroSerializer] = {}
        self.registered_schemas: Dict[str, int] = {}  # Track registered schema IDs
        self.resolved_schemas: Dict[
            str, Dict
        ] = {}  # Fully resolved schemas for serialization
        self._started = False

    def start(self) -> None:
        """
        Initialize the producer and schema registry client.
        """
        if self._started:
            logger.warning("Schema Registry producer already started")
            return

        try:
            # Initialize Schema Registry client
            schema_registry_conf = {"url": settings.SCHEMA_REGISTRY_URL}

            if (
                hasattr(settings, "SCHEMA_REGISTRY_API_KEY")
                and settings.SCHEMA_REGISTRY_API_KEY
            ):
                schema_registry_conf["basic.auth.user.info"] = (
                    f"{settings.SCHEMA_REGISTRY_API_KEY}:{settings.SCHEMA_REGISTRY_API_SECRET}"
                )

            self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)

            # Register schemas with proper dependency handling
            self._register_schemas()

            # Configure producer
            producer_conf = {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "acks": settings.KAFKA_ACKS,
                "enable.idempotence": settings.KAFKA_ENABLE_IDEMPOTENCE,
            }

            self.producer = Producer(producer_conf)
            self._started = True

            logger.info("Schema Registry producer started successfully")

        except Exception as e:
            logger.error(
                f"Failed to start Schema Registry producer: {e}", exc_info=True
            )
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
        """
        Register all schemas with proper dependency handling.
        Uses schema references to handle nested types.
        """
        # Step 1: Register base schemas first
        base_schemas = {k: v for k, v in TOPIC_SCHEMAS.items() if k.startswith("_base")}

        for topic_suffix, schema_dict in base_schemas.items():
            schema_name = schema_dict.get("name")
            namespace = schema_dict.get("namespace", "com.todo_reminder.events")
            subject = f"{namespace}.{schema_name}"

            # Register with Schema Registry
            schema_id = self._register_base_schema(subject, schema_dict)
            self.registered_schemas[subject] = schema_id

            # Cache parsed schema
            self.parsed_schemas[subject] = schema_dict

        # Step 2: Register event schemas with references
        event_schemas = {
            k: v for k, v in TOPIC_SCHEMAS.items() if not k.startswith("_base")
        }

        for topic_suffix, schema_dict in event_schemas.items():
            full_topic = f"{settings.KAFKA_TOPIC_PREFIX}.{topic_suffix}"
            subject = f"{full_topic}-value"

            # Build the schema with references
            references = self._build_references(schema_dict)

            schema_id = self._register_event_schema(subject, schema_dict, references)
            self.registered_schemas[subject] = schema_id

            # Parse schema to resolve Avro dependencies then create serializer for this topic
            # parsed_schema = self._parse_schema_with_dependencies(schema_dict)
            # self._create_serializer(topic_suffix, parsed_schema)
            # Resolve schema with all dependencies inlined
            try:
                resolved_schema = self._resolve_schema_references(schema_dict)
                self.resolved_schemas[topic_suffix] = resolved_schema

                # Create serializer with fully resolved schema
                self._create_serializer(topic_suffix, resolved_schema)

                logger.info(f"✅ Registered and created serializer for: {topic_suffix}")

            except Exception as e:
                logger.error(
                    f"❌ Failed to resolve/serialize schema for {topic_suffix}: {e}",
                    exc_info=True,
                )
                raise

    def _register_base_schema(self, subject: str, schema_dict: dict) -> int:
        """
        Register a base schema (like EventMetadata).

        Args:
            subject: Subject name (e.g., "com.todo_reminder.events.EventMetadata")
            schema_dict: Schema definition

        Returns:
            Schema ID
        """
        try:
            schema_str = json.dumps(schema_dict)

            # Create Schema object
            schema = Schema(schema_str=schema_str, schema_type="AVRO", references=[])

            # Register
            schema_id = self.schema_registry_client.register_schema(
                subject_name=subject, schema=schema
            )

            logger.info(f"✅ Registered base schema {subject} with ID: {schema_id}")
            return schema_id

        except Exception as e:
            logger.error(
                f"❌ Failed to register base schema {subject}: {e}", exc_info=True
            )
            raise

    def _register_event_schema(
        self, subject: str, schema_dict: dict, references: List[Dict[str, Any]]
    ) -> int:
        """
        Register an event schema with references to base schemas.

        Args:
            subject: Subject name
            schema_dict: Schema definition
            references: List of schema references

        Returns:
            Schema ID
        """
        try:
            schema_str = json.dumps(schema_dict)

            # Create Schema object with references
            from confluent_kafka.schema_registry import SchemaReference

            schema_refs = []
            for ref in references:
                schema_refs.append(
                    SchemaReference(
                        name=ref["name"], subject=ref["subject"], version=ref["version"]
                    )
                )

            schema = Schema(
                schema_str=schema_str, schema_type="AVRO", references=schema_refs
            )

            # Register
            schema_id = self.schema_registry_client.register_schema(
                subject_name=subject, schema=schema
            )

            logger.info(f"✅ Registered event schema {subject} with ID: {schema_id}")
            return schema_id

        except Exception as e:
            logger.error(
                f"❌ Failed to register event schema {subject}: {e}", exc_info=True
            )
            raise

    def _build_references(self, schema_dict: dict) -> List[Dict[str, Any]]:
        """
        Build list of schema references by scanning for string type references.

        Args:
            schema_dict: Schema to scan

        Returns:
            List of references
        """
        references = []
        seen = set()

        def scan_fields(fields):
            for field in fields:
                field_type = field.get("type")

                # Check if it's a string reference (fully qualified name)
                if isinstance(field_type, str) and "." in field_type:
                    if field_type not in seen:
                        seen.add(field_type)
                        # This is a reference to another schema
                        references.append(
                            {
                                "name": field_type,
                                "subject": field_type,
                                "version": 1,  # Use version 1
                            }
                        )

                # Check union types
                elif isinstance(field_type, list):
                    for union_type in field_type:
                        if isinstance(union_type, str) and "." in union_type:
                            if union_type not in seen:
                                seen.add(union_type)
                                references.append(
                                    {
                                        "name": union_type,
                                        "subject": union_type,
                                        "version": 1,
                                    }
                                )

        # Scan top-level fields
        if "fields" in schema_dict:
            scan_fields(schema_dict["fields"])

        return references

    def _resolve_schema_references(self, schema_dict: dict) -> dict:
        """
        Resolve all schema references by inlining referenced schemas.

        This creates a self-contained schema with all nested types defined inline.
        """
        resolved = copy.deepcopy(schema_dict)

        def resolve_type(type_def):
            """Recursively resolve type definitions."""
            if isinstance(type_def, str):
                # Check if it's a reference to a named schema
                if "." in type_def and type_def in self.parsed_schemas:
                    # Return the full schema definition
                    return copy.deepcopy(self.parsed_schemas[type_def])
                return type_def

            elif isinstance(type_def, list):
                # Union type - resolve each option
                return [resolve_type(t) for t in type_def]

            elif isinstance(type_def, dict):
                # Complex type - resolve nested fields
                if type_def.get("type") == "record":
                    resolved_record = copy.deepcopy(type_def)
                    if "fields" in resolved_record:
                        for field in resolved_record["fields"]:
                            field["type"] = resolve_type(field["type"])
                    return resolved_record

                elif type_def.get("type") == "array":
                    resolved_array = copy.deepcopy(type_def)
                    resolved_array["items"] = resolve_type(resolved_array["items"])
                    return resolved_array

                elif type_def.get("type") == "map":
                    resolved_map = copy.deepcopy(type_def)
                    resolved_map["values"] = resolve_type(resolved_map["values"])
                    return resolved_map

                return type_def

            return type_def

        # Resolve all field types
        if "fields" in resolved:
            for field in resolved["fields"]:
                field["type"] = resolve_type(field["type"])

        return resolved

    def _create_serializer(self, topic_suffix: str, schema_dict: dict) -> None:
        """
        Create Avro serializer for a topic.

        Args:
            topic_suffix: Topic name
            schema_dict: Schema definition
        """
        try:
            # For serializer, we need to provide the full schema with resolved types
            schema_str = json.dumps(schema_dict)

            self.serializers[topic_suffix] = AvroSerializer(
                self.schema_registry_client, schema_str, lambda obj, ctx: obj
            )

            logger.debug(f"✅ Created serializer for {topic_suffix}")

        except Exception as e:
            logger.error(
                f"❌ Failed to create serializer for {topic_suffix}: {e}", exc_info=True
            )
            raise

    def _parse_schema_with_dependencies(self, schema_dict: dict) -> Schema:
        """
        Parse schema to resolve types for Avro serialization

        Args:
            schema_dict (str): Schema definition

        Returns:
            Schema: Parsed schema ready to be serialized
        """
        named_schemas = self.parsed_schemas.copy()

        # Parse the schema with fastavro, providing named schemas for reference resolution
        try:
            parsed_schema = fastavro.parse_schema(
                schema_dict, named_schemas=named_schemas
            )
            return parsed_schema
        except Exception as e:
            logger.error(f"Failed to parse schema: {e}", exc_info=True)
            logger.error(f"Schema: {json.dumps(schema_dict, indent=2)}")
            logger.error(f"Named schemas available: {list(named_schemas.keys())}")
            raise

    def send_event(
        self,
        topic: str,
        event: Union[BaseModel, Dict[str, Any]],
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
            # Manually serialize the value using AvroSerializer
            serialization_context = SerializationContext(
                topic=full_topic, field=MessageField.VALUE
            )

            # Serialize value to bytes
            serialized_value = serializer(event_dict, serialization_context)

            # Serialize key to bytes (simple UTF-8 encoding)
            serialized_key = key.encode("utf-8") if key else None

            self.producer.produce(
                topic=full_topic,
                key=serialized_key,
                value=serialized_value,
                on_delivery=callback or self._delivery_report,
            )

            self.producer.poll(0)

            logger.info(f"Event sent to {full_topic} (key: {key})")

        except Exception as e:
            logger.error(f"Failed to send event to {full_topic}: {e}", exc_info=True)
            raise

    def flush(self, timeout: float = 10.0) -> None:
        """Flush pending messages."""
        if self.producer:
            remaining = self.producer.flush(timeout)
            if remaining > 0:
                logger.warning(f"{remaining} messages were not delivered")

    @staticmethod
    def _delivery_report(err, msg):
        """Default delivery report callback."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[partition {msg.partition()}] at offset {msg.offset()}"
            )


schema_registry_producer = SchemaRegistryProducerService()

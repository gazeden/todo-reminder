FROM confluentinc/cp-kafka-connect:8.0.3

# Metadata
LABEL description="Custom Kafka Connect with pre-installed connectors"

# Install connectors
RUN confluent-hub install --no-prompt debezium/debezium-connector-postgresql:3.1.2

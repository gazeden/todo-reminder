#!/bin/bash
set -e

echo "Waiting for Kafka Connect to start..."
while [ $(curl -s -o /dev/null -w %{http_code} http://localhost:8083/) -ne 200 ]; do
  sleep 5
done

echo "Kafka Connect is ready!"

if [ -d /etc/kafka-connect/connectors ]; then
  echo "Loading connectors from /etc/kafka-connect/connectors..."
  
  for connector_file in /etc/kafka-connect/connectors/*.json; do
    if [ -f "$connector_file" ]; then
      connector_name=$(jq -r '.name' "$connector_file")
      
      if curl -s http://localhost:8083/connectors | grep -q "\"$connector_name\""; then
        echo "✓ Connector '$connector_name' already exists"
      else
        echo "→ Creating connector '$connector_name'..."
        
        response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8083/connectors \
          -H "Content-Type: application/json" \
          -d @"$connector_file")
        
        http_code=$(echo "$response" | tail -n1)
        
        if [ "$http_code" -eq 201 ] || [ "$http_code" -eq 200 ]; then
          echo "✓ Successfully created connector '$connector_name'"
        else
          echo "✗ Failed to create connector '$connector_name' (HTTP $http_code)"
        fi
      fi
    fi
  done
fi

echo "Connector loading complete!"
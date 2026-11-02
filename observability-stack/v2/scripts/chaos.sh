#!/bin/bash

echo "🔥 Starting chaos engineering..."

SERVICES=("auth_service" "payment_service" "inventory_service")

while true; do
  # Random service
  SERVICE=${SERVICES[$RANDOM % ${#SERVICES[@]}]}
  
  echo "💥 Killing $SERVICE..."
  docker restart $SERVICE
  
  echo "⏳ Waiting 60 seconds..."
  sleep 60
  
  echo "✅ $SERVICE recovered"
  echo ""
done
#!/bin/bash

echo "🚀 Starting load test..."

# Register user
echo "Registering user..."
curl -s -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "loadtest", "password": "test123"}' > /dev/null

# Login
echo "Logging in..."
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "loadtest", "password": "test123"}' \
  | jq -r '.token')

echo "Token obtained: ${TOKEN:0:20}..."

# Generate load
echo "Generating load (100 requests)..."
for i in {1..100}; do
  # Make payment
  curl -s -X POST http://localhost/api/v1/payment/charge \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"amount\": $((RANDOM % 100 + 10))}" &
  
  # Get products
  curl -s http://localhost/api/v1/inventory/products > /dev/null &
  
  # Reserve stock
  PRODUCT_ID=$((RANDOM % 5 + 1))
  curl -s -X POST http://localhost/api/v1/inventory/product/$PRODUCT_ID/reserve \
    -H "Content-Type: application/json" \
    -d '{"quantity": 1}' > /dev/null &
  
  # Rate limit
  if [ $((i % 10)) -eq 0 ]; then
    echo "Progress: $i/100"
    sleep 0.5
  fi
done

wait
echo "✅ Load test complete!"
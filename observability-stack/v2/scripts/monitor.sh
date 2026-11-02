#!/bin/bash

echo "📊 System Monitor"
echo "================="
echo ""

while true; do
  clear
  echo "📊 Observability Stack Status - $(date)"
  echo "========================================="
  echo ""
  
  # Service status
  echo "🔧 Services:"
  docker compose ps --format "table {{.Name}}\t{{.Status}}"
  echo ""
  
  # Resource usage
  echo "💾 Resource Usage:"
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
    auth_service payment_service inventory_service redis postgres rabbitmq
  echo ""
  
  # Redis stats
  echo "💨 Cache Hit Rate:"
  REDIS_HITS=$(docker exec redis redis-cli INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
  REDIS_MISSES=$(docker exec redis redis-cli INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
  if [ ! -z "$REDIS_HITS" ] && [ ! -z "$REDIS_MISSES" ]; then
    TOTAL=$((REDIS_HITS + REDIS_MISSES))
    if [ $TOTAL -gt 0 ]; then
      HIT_RATE=$((REDIS_HITS * 100 / TOTAL))
      echo "  Hit Rate: ${HIT_RATE}%"
    fi
  fi
  echo ""
  
  # Queue depth
  echo "📬 RabbitMQ Queue Depth:"
  docker exec rabbitmq rabbitmqctl list_queues 2>/dev/null | grep payment_events || echo "  No messages"
  echo ""
  
  sleep 5
done
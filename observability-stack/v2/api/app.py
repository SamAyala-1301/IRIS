from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram
import psycopg2
import psycopg2.extras
import redis
import json
import random
import logging
import os
import time

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.resources import Resource

# Initialize Flask
app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics for cache
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
cache_operation_duration = Histogram('cache_operation_duration_seconds', 'Cache operation duration')

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# OpenTelemetry setup
resource = Resource(attributes={
    "service.name": "flask-api",
    "service.version": "2.0.0"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

otlp_exporter = OTLPSpanExporter(
    endpoint="http://otel-collector:4318/v1/traces",
    timeout=30
)

span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

tracer = trace.get_tracer(__name__)

# Auto-instrument
FlaskInstrumentor().instrument_app(app)
Psycopg2Instrumentor().instrument()

logger.info("OpenTelemetry tracing initialized")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'transactions'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
CACHE_TTL = 300  # 5 minutes

# Initialize Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

def get_db_connection():
    """Create database connection with retry logic"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts")
                raise

@app.route("/health")
def health():
    """Deep health check with database and cache connectivity"""
    health_status = {
        "status": "healthy",
        "service": "flask_api",
        "checks": {}
    }
    
    # Check database connection
    try:
        with tracer.start_as_current_span("health_check_db"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis connection
    try:
        with tracer.start_as_current_span("health_check_redis"):
            if redis_client:
                redis_client.ping()
                health_status["checks"]["redis"] = "ok"
            else:
                health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"error: {str(e)}"
        logger.error(f"Redis health check failed: {e}")
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@app.route("/transactions")
def get_transactions():
    """Get recent transactions with Redis caching"""
    try:
        with tracer.start_as_current_span("fetch_transactions") as span:
            cache_key = "transactions:recent:10"
            
            # Try cache first
            if redis_client:
                with tracer.start_as_current_span("redis_get"):
                    with cache_operation_duration.time():
                        cached_data = redis_client.get(cache_key)
                
                if cached_data:
                    cache_hits.inc()
                    span.set_attribute("cache.hit", True)
                    logger.info("Cache HIT for recent transactions")
                    return jsonify(json.loads(cached_data)), 200
                else:
                    cache_misses.inc()
                    span.set_attribute("cache.hit", False)
                    logger.info("Cache MISS for recent transactions")
            
            # Cache miss - query database
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            with tracer.start_as_current_span("db_query_transactions"):
                cur.execute("""
                    SELECT id, amount, status, user_id, created_at 
                    FROM transactions 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                transactions = cur.fetchall()
                span.set_attribute("transaction.count", len(transactions))
            
            cur.close()
            conn.close()
            
            # Convert to JSON-serializable format
            result = []
            for tx in transactions:
                result.append({
                    'id': tx['id'],
                    'amount': float(tx['amount']),
                    'status': tx['status'],
                    'user_id': tx['user_id'],
                    'created_at': tx['created_at'].isoformat() if tx['created_at'] else None
                })
            
            response_data = {"transactions": result, "count": len(result), "source": "database"}
            
            # Store in cache
            if redis_client:
                with tracer.start_as_current_span("redis_set"):
                    with cache_operation_duration.time():
                        redis_client.setex(
                            cache_key,
                            CACHE_TTL,
                            json.dumps(response_data)
                        )
                logger.info(f"Cached {len(result)} transactions for {CACHE_TTL}s")
            
            return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Failed to retrieve transactions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/transactions/create", methods=['POST'])
def create_transaction():
    """Create a new transaction and invalidate cache"""
    try:
        with tracer.start_as_current_span("create_transaction") as span:
            # Simulate occasional errors (5% error rate)
            if random.random() < 0.05:
                span.set_attribute("error", True)
                raise Exception("Payment gateway timeout")
            
            # Simulate payment processing delay
            with tracer.start_as_current_span("payment_gateway"):
                time.sleep(random.uniform(0.05, 0.2))
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Generate random transaction
            amount = round(random.uniform(10.0, 999.99), 2)
            user_id = f"user_{random.randint(1, 1000):03d}"
            status = random.choice(['completed', 'completed', 'completed', 'pending'])
            
            span.set_attribute("transaction.amount", amount)
            span.set_attribute("transaction.status", status)
            span.set_attribute("transaction.user_id", user_id)
            
            with tracer.start_as_current_span("db_insert_transaction"):
                cur.execute(
                    "INSERT INTO transactions (amount, status, user_id) VALUES (%s, %s, %s) RETURNING id",
                    (amount, status, user_id)
                )
                tx_id = cur.fetchone()[0]
                conn.commit()
            
            cur.close()
            conn.close()
            
            # Invalidate cache
            if redis_client:
                with tracer.start_as_current_span("redis_delete"):
                    redis_client.delete("transactions:recent:10")
                logger.info("Invalidated transaction cache")
            
            logger.info(f"Transaction {tx_id} created: ${amount} - {status}")
            
            return jsonify({
                "transaction_id": tx_id,
                "amount": amount,
                "status": status,
                "user_id": user_id
            }), 201
    
    except Exception as e:
        logger.error(f"Transaction creation failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    if not redis_client:
        return jsonify({"error": "Redis not configured"}), 503
    
    try:
        info = redis_client.info()
        stats = {
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": 0
        }
        
        # Calculate hit rate
        total = stats["keyspace_hits"] + stats["keyspace_misses"]
        if total > 0:
            stats["hit_rate"] = round((stats["keyspace_hits"] / total) * 100, 2)
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cache/clear", methods=['POST'])
def clear_cache():
    """Clear all cache"""
    if not redis_client:
        return jsonify({"error": "Redis not configured"}), 503
    
    try:
        redis_client.flushdb()
        logger.info("Cache cleared")
        return jsonify({"message": "Cache cleared successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/error")
def error():
    """Intentional error endpoint for testing alerts"""
    raise Exception("Intentional error for testing")

if __name__ == "__main__":
    logger.info("Starting Flask API v2.0 with Redis caching on port 8000")
    app.run(host="0.0.0.0", port=8000)
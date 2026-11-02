from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram
import requests
import psycopg2
import psycopg2.extras
import random
import time
import os
import json
import pika

# OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from prometheus_client import Gauge

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics
payment_amount = Counter('payment_amount_total_cents', 'Total payment amount in cents')
payment_transactions = Counter('payment_transactions_total', 'Total payment transactions', ['status'])

# Business metrics
revenue_gauge = Gauge('business_revenue_total_dollars', 'Total revenue in dollars')
active_users_gauge = Gauge('business_active_users', 'Currently active users')

# OpenTelemetry setup
resource = Resource(attributes={"service.name": "payment-service"})

trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
FlaskInstrumentor().instrument_app(app)
tracer = trace.get_tracer(__name__)

AUTH_SERVICE = "http://auth_service:8001"
DB_CONFIG = {
    'host': 'postgres',
    'database': 'transactions',
    'user': 'postgres',
    'password': 'postgres'
}

def publish_payment_event(payment_data):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', credentials=pika.PlainCredentials('admin', 'admin'))
        )
        channel = connection.channel()
        channel.queue_declare(queue='payment_events', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='payment_events',
            body=json.dumps(payment_data),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        connection.close()
        print(f"Published payment event: {payment_data}")
    except Exception as e:
        print(f"Failed to publish event: {e}")

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def verify_token(token):
    with tracer.start_as_current_span("verify_auth_token"):
        try:
            response = requests.post(
                f"{AUTH_SERVICE}/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Auth verification failed: {e}")
            return None

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "payment"}), 200

@app.route("/charge", methods=['POST'])
def charge():
    with tracer.start_as_current_span("process_payment") as span:
        # Get token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({"error": "Authorization required"}), 401
        
        # Verify user
        user_data = verify_token(token)
        if not user_data:
            return jsonify({"error": "Invalid token"}), 401
        
        user_id = user_data['user_id']
        span.set_attribute("user_id", user_id)
        
        # Get payment details
        data = request.json
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        span.set_attribute("payment.amount", amount)
        
        # Simulate payment gateway (10% failure rate)
        with tracer.start_as_current_span("payment_gateway"):
            time.sleep(random.uniform(0.1, 0.3))  # Simulate network delay
            
            if random.random() < 0.1:
                payment_transactions.labels(status='failed').inc()
                span.set_attribute("payment.status", "failed")
                return jsonify({
                    "error": "Payment gateway timeout",
                    "status": "failed"
                }), 500
        
        # Store in database
        with tracer.start_as_current_span("store_payment"):
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO transactions (amount, status, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (amount, 'completed', user_id))
            
            payment_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
        
        # Update metrics
        payment_amount.inc(amount * 100)  # Convert to cents
        payment_transactions.labels(status='success').inc()
        
        span.set_attribute("payment.id", payment_id)
        span.set_attribute("payment.status", "success")

        conn_metrics = get_db()
        cur_metrics = conn_metrics.cursor()
        cur_metrics.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed'")
        total_revenue = cur_metrics.fetchone()[0] or 0
        revenue_gauge.set(float(total_revenue))
        cur_metrics.close()
        conn_metrics.close()
        
        # Publish event to queue
        with tracer.start_as_current_span("publish_event"):
            publish_payment_event({
                "payment_id": payment_id,
                "user_id": user_id,
                "amount": amount,
                "status": "completed"
            })
        return jsonify({
            "payment_id": payment_id,
            "amount": amount,
            "status": "completed",
            "user_id": user_id
        }), 201

@app.route("/payment/<int:payment_id>")
def get_payment(payment_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Authorization required"}), 401
    
    user_data = verify_token(token)
    if not user_data:
        return jsonify({"error": "Invalid token"}), 401
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT id, amount, status, user_id, created_at
        FROM transactions
        WHERE id = %s
    """, (payment_id,))
    
    payment = cur.fetchone()
    cur.close()
    conn.close()
    
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    
    return jsonify({
        "id": payment['id'],
        "amount": float(payment['amount']),
        "status": payment['status'],
        "user_id": payment['user_id'],
        "created_at": payment['created_at'].isoformat()
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
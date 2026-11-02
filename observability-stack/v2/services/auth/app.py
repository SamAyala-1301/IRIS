from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import jwt
import redis
import json
import hashlib
import time
import os
from prometheus_client import Gauge

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource

app = Flask(__name__)
metrics = PrometheusMetrics(app)
active_sessions = Gauge('auth_active_sessions', 'Number of active user sessions')

# OpenTelemetry setup
resource = Resource(attributes={"service.name": "auth-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
FlaskInstrumentor().instrument_app(app)
tracer = trace.get_tracer(__name__)

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

users_db = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "auth"}), 200

@app.route("/register", methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    if username in users_db:
        return jsonify({"error": "User already exists"}), 400
    
    user_id = f"user_{len(users_db) + 1}"
    users_db[username] = {
        "user_id": user_id,
        "password_hash": hash_password(password),
        "created_at": time.time()
    }
    
    return jsonify({
        "user_id": user_id,
        "username": username
    }), 201

@app.route("/login", methods=['POST'])
def login():
    with tracer.start_as_current_span("login_user"):
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if username not in users_db:
            return jsonify({"error": "Invalid credentials"}), 401
        
        user = users_db[username]
        if user['password_hash'] != hash_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Generate JWT
        token = jwt.encode({
            "user_id": user['user_id'],
            "username": username,
            "exp": time.time() + 3600
        }, SECRET_KEY, algorithm="HS256")
        
        # Store session in Redis
        with tracer.start_as_current_span("store_session_redis"):
            redis_client.setex(f"session:{token}", 3600, user['user_id'])
        
        return jsonify({
            "token": token,
            "user_id": user['user_id']
        }), 200

@app.route("/verify", methods=['POST'])
def verify():
    with tracer.start_as_current_span("verify_token"):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({"error": "No token provided"}), 401
        
        # Check Redis session
        with tracer.start_as_current_span("check_redis_session"):
            user_id = redis_client.get(f"session:{token}")
        
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return jsonify({
                "valid": True,
                "user_id": payload['user_id'],
                "username": payload['username']
            }), 200
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

@app.route("/stats")
def get_stats():
    keys = redis_client.keys("session:*")
    active_sessions.set(len(keys))
    
    return jsonify({
        "active_sessions": len(keys),
        "total_users": len(users_db)
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
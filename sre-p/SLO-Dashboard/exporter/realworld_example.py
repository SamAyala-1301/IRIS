# realworld_example/claims_api_instrumented.py
#
# This is what a REAL claims-api would look like with full observability wired in.
# Three signals: metrics (Prometheus), structured logs (structlog), traces (OpenTelemetry)
# Run with: pip install flask prometheus-client structlog opentelemetry-sdk
#           opentelemetry-instrumentation-flask opentelemetry-exporter-otlp-proto-grpc
# Then: python claims_api_instrumented.py

import time
import random
import logging
import structlog                          # structured logging — JSON output, not plain text
from flask import Flask, jsonify, request, g

# ── SIGNAL 1: METRICS ─────────────────────────────────────────────────────────
# prometheus_client maintains in-memory counters/gauges/histograms.
# When Prometheus scrapes /metrics, it reads these values.
# Nothing is "pushed" — Prometheus comes to us every 15s.
from prometheus_client import (
    Counter, Histogram, Gauge,
    make_wsgi_app, multiprocess, CollectorRegistry
)
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Counter: only goes up. Good for requests, errors, retries.
REQUEST_COUNT = Counter(
    'claims_api_requests_total',          # metric name
    'Total HTTP requests to claims-api',  # description
    ['method', 'endpoint', 'status']      # label dimensions — every unique combo = one time series
)

# Histogram: records distribution of values. Buckets define resolution.
# This gives you p50, p95, p99 via histogram_quantile() in PromQL.
REQUEST_LATENCY = Histogram(
    'claims_api_request_duration_seconds',
    'HTTP request latency',
    ['endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.8, 1.0, 2.0, 5.0]
    # ^ these are your SLO boundaries — 0.8s is our p99 target for claims-api
)

# Gauge: can go up or down. Good for queue depth, active connections, current state.
ACTIVE_CLAIMS = Gauge(
    'claims_api_active_processing',
    'Claims currently being processed'
)

CLAIM_VALUE = Histogram(
    'claims_api_claim_value_usd',
    'Distribution of claim values submitted',
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

# ── SIGNAL 2: STRUCTURED LOGS ─────────────────────────────────────────────────
# structlog outputs JSON instead of plain text.
# Every log line has: timestamp, level, event, plus any fields you bind.
# The trace_id field is the critical link — it connects a log line to a trace.
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()   # output as JSON, not plain text
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
log = structlog.get_logger()

# ── SIGNAL 3: TRACES (OpenTelemetry) ──────────────────────────────────────────
# OTel wraps each request in a "span" — a unit of work with a start time,
# end time, and any attributes you attach.
# The tracer sends spans to an OTel collector on port 4317 (gRPC).
# If you're using Datadog: the DD agent receives these and correlates them.
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# TracerProvider is the factory for tracers.
# ConsoleSpanExporter prints spans to stdout so you can see them locally.
# In production you'd swap this for OTLPSpanExporter pointing at your collector.
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
    # ^ In production: BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("claims-api")   # name your tracer after your service

# ── FLASK APP ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# FlaskInstrumentor auto-creates a span for every incoming request.
# You don't need to manually start/end spans for HTTP handlers — it's automatic.
# This is what "auto-instrumentation" means.
FlaskInstrumentor().instrument_app(app)

# ── MIDDLEWARE: record metrics on every request ────────────────────────────────
@app.before_request
def start_timer():
    g.start_time = time.time()            # store start time in Flask's request context

@app.after_request
def record_metrics(response):
    duration = time.time() - g.start_time

    # Get the current trace_id so we can inject it into logs
    # This is the critical correlation link between logs and traces
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, '032x') if span else "no-trace"

    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=str(response.status_code)
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.path).observe(duration)

    # Structured log with trace_id injected — this is what Datadog uses to
    # show you the log line right next to the trace waterfall
    log.info(
        "http_request",                   # event name
        method=request.method,
        path=request.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
        trace_id=trace_id,                # ← the correlation key
        service="claims-api",
        env="production"
    )
    return response

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route('/claims', methods=['POST'])
def submit_claim():
    ACTIVE_CLAIMS.inc()                   # gauge: one more claim being processed
    try:
        # Simulate processing time — this is what your histogram will capture
        processing_time = random.uniform(0.05, 0.9)
        time.sleep(processing_time)

        # Create a child span for the "validate" step — manual instrumentation
        # Use this for any operation inside a request you want to measure separately
        with tracer.start_as_current_span("validate-claim") as span:
            claim_value = random.uniform(100, 50000)
            CLAIM_VALUE.observe(claim_value)

            # Attach attributes to the span — searchable in Datadog/NR trace UI
            span.set_attribute("claim.value_usd", claim_value)
            span.set_attribute("claim.type", "auto")
            span.set_attribute("claim.policy_id", f"POL-{random.randint(1000,9999)}")

            # Simulate occasional validation failures
            if random.random() < 0.03:    # 3% error rate
                span.set_attribute("error", True)
                log.warning(
                    "claim_validation_failed",
                    claim_value=claim_value,
                    reason="policy_limit_exceeded"
                )
                return jsonify({"error": "Policy limit exceeded"}), 422

        claim_id = f"CLM-{random.randint(10000, 99999)}"
        log.info("claim_submitted", claim_id=claim_id, value=claim_value)
        return jsonify({"claim_id": claim_id, "status": "processing"}), 202

    finally:
        ACTIVE_CLAIMS.dec()               # gauge: one less claim being processed

@app.route('/claims/<claim_id>', methods=['GET'])
def get_claim(claim_id):
    # Simulate DB lookup latency
    time.sleep(random.uniform(0.01, 0.15))

    if random.random() < 0.01:            # 1% not found
        log.warning("claim_not_found", claim_id=claim_id)
        return jsonify({"error": "Claim not found"}), 404

    return jsonify({
        "claim_id": claim_id,
        "status": random.choice(["processing", "approved", "rejected"]),
        "updated_at": "2024-01-15T10:30:00Z"
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "claims-api"})

# ── METRICS ENDPOINT ──────────────────────────────────────────────────────────
# This mounts /metrics on a separate WSGI app.
# Prometheus scrapes this endpoint every 15s.
# The response is plain text — not JSON. That's the Prometheus exposition format.
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    log.info("claims_api_starting", port=5000, metrics_port=5000)
    # /metrics available at http://localhost:5000/metrics
    # /claims available at http://localhost:5000/claims
    app.run(host='0.0.0.0', port=5000, debug=False)
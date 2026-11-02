"""OpenTelemetry configuration generator."""
from typing import Dict, List

class OTelConfigGenerator:
    """Generate OpenTelemetry configuration for different frameworks."""
    
    def __init__(self):
        self.otel_collector_endpoint = "http://otel-collector:4317"
        self.metrics_port = 9090
        self.service_name_prefix = "obs-stack"
    
    def generate_python_otel_init(self, framework: str, service_name: str) -> str:
        """
        Generate Python OpenTelemetry initialization code.
        
        This code will be injected into the container.
        """
        return f'''"""Auto-generated OpenTelemetry instrumentation by ObsStack."""
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

# Service identification
resource = Resource.create({{
    "service.name": "{service_name}",
    "service.framework": "{framework}",
    "service.instrumented_by": "obs-stack-v3"
}})

# Tracing setup
trace_provider = TracerProvider(resource=resource)
trace_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "{self.otel_collector_endpoint}"))
)
trace_provider.add_span_processor(trace_processor)
trace.set_tracer_provider(trace_provider)

# Metrics setup
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "{self.otel_collector_endpoint}"))
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

print("✅ OpenTelemetry initialized by ObsStack")
'''
    
    def generate_flask_instrumentation(self) -> str:
        """Generate Flask-specific instrumentation code."""
        return '''
# Flask auto-instrumentation
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def instrument_flask_app(app):
    """Instrument Flask application."""
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    print("✅ Flask instrumented by ObsStack")
    return app
'''
    
    def generate_django_instrumentation(self) -> str:
        """Generate Django-specific instrumentation code."""
        return '''
# Django auto-instrumentation
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

DjangoInstrumentor().instrument()
RequestsInstrumentor().instrument()
print("✅ Django instrumented by ObsStack")
'''
    
    def generate_fastapi_instrumentation(self) -> str:
        """Generate FastAPI-specific instrumentation code."""
        return '''
# FastAPI auto-instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def instrument_fastapi_app(app):
    """Instrument FastAPI application."""
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    print("✅ FastAPI instrumented by ObsStack")
    return app
'''
    
    def generate_nodejs_otel_init(self, framework: str, service_name: str) -> str:
        """Generate Node.js OpenTelemetry initialization code."""
        return f'''// Auto-generated OpenTelemetry instrumentation by ObsStack
const {{ NodeTracerProvider }} = require('@opentelemetry/sdk-trace-node');
const {{ Resource }} = require('@opentelemetry/resources');
const {{ SemanticResourceAttributes }} = require('@opentelemetry/semantic-conventions');
const {{ OTLPTraceExporter }} = require('@opentelemetry/exporter-trace-otlp-grpc');
const {{ BatchSpanProcessor }} = require('@opentelemetry/sdk-trace-base');
const {{ registerInstrumentations }} = require('@opentelemetry/instrumentation');
const {{ HttpInstrumentation }} = require('@opentelemetry/instrumentation-http');
const {{ ExpressInstrumentation }} = require('@opentelemetry/instrumentation-express');

// Service identification
const resource = Resource.default().merge(
  new Resource({{
    [SemanticResourceAttributes.SERVICE_NAME]: "{service_name}",
    "service.framework": "{framework}",
    "service.instrumented_by": "obs-stack-v3"
  }})
);

// Tracing setup
const provider = new NodeTracerProvider({{ resource }});
const exporter = new OTLPTraceExporter({{
  url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || "{self.otel_collector_endpoint}"
}});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();

// Auto-instrument
registerInstrumentations({{
  instrumentations: [
    new HttpInstrumentation(),
    new ExpressInstrumentation(),
  ],
}});

console.log("✅ OpenTelemetry initialized by ObsStack");
'''
    
    def generate_requirements_additions(self, framework: str) -> List[str]:
        """Generate Python packages to add to requirements.txt."""
        base_packages = [
            "opentelemetry-api>=1.21.0",
            "opentelemetry-sdk>=1.21.0",
            "opentelemetry-exporter-otlp>=1.21.0",
        ]
        
        framework_packages = {
            "flask": ["opentelemetry-instrumentation-flask>=0.42b0"],
            "django": ["opentelemetry-instrumentation-django>=0.42b0"],
            "fastapi": ["opentelemetry-instrumentation-fastapi>=0.42b0"],
        }
        
        return base_packages + framework_packages.get(framework, [])
    
    def generate_package_json_additions(self, framework: str) -> Dict[str, str]:
        """Generate Node.js packages to add to package.json."""
        base_packages = {
            "@opentelemetry/sdk-trace-node": "^1.17.0",
            "@opentelemetry/resources": "^1.17.0",
            "@opentelemetry/semantic-conventions": "^1.17.0",
            "@opentelemetry/exporter-trace-otlp-grpc": "^0.43.0",
            "@opentelemetry/sdk-trace-base": "^1.17.0",
            "@opentelemetry/instrumentation": "^0.43.0",
            "@opentelemetry/instrumentation-http": "^0.43.0",
        }
        
        framework_packages = {
            "express": {"@opentelemetry/instrumentation-express": "^0.33.0"},
            "nestjs": {"@opentelemetry/instrumentation-nestjs-core": "^0.33.0"},
        }
        
        return {**base_packages, **framework_packages.get(framework, {})}
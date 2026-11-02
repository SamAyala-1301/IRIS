Getting Started with ObsStack V3
What is ObsStack?
ObsStack V3 is an instant observability platform that automatically detects your application's framework and adds comprehensive monitoring with zero code changes.

Key Features
🔍 Auto-Detection: Identifies 6+ frameworks automatically
🎯 Auto-Instrumentation: Adds OpenTelemetry in seconds
📊 Auto-Dashboards: Framework-specific Grafana dashboards
🚨 Smart Alerts: Pre-configured alerting rules
⚡ <5% Overhead: Minimal performance impact
🐳 Docker Native: Seamless container integration
Quick Start (5 Minutes)
Prerequisites
Docker & Docker Compose installed
Python 3.8+ installed
4GB+ RAM available
10GB+ disk space
Installation
bash
# Clone repository
git clone https://github.com/your-org/obs-stack-v3
cd obs-stack-v3/v3

# Install
pip install -e .

# Verify
obs-stack version
Initialize
bash
# Navigate to your project
cd /path/to/your/project

# Initialize ObsStack
obs-stack init

# This creates:
# - backend/ (observability stack)
# - .obsstack/ (configuration)
# - obs-stack.yml (if you have docker-compose.yml)
Start Observability Stack
bash
obs-stack up

# Services starting:
# ✓ Prometheus (metrics)
# ✓ Grafana (dashboards)
# ✓ Loki (logs)
# ✓ Tempo (traces)
# ✓ OpenTelemetry Collector
Access Dashboards
Open Grafana at http://localhost:3001

Username: admin
Password: obsstack
Instrument Your Applications
bash
# Detect all running containers
obs-stack detect-all

# Instrument specific container
obs-stack instrument my-flask-app

# Or instrument all at once
obs-stack instrument-all

# Generate dashboards
obs-stack dashboard --all
View Your Metrics
Open Grafana: http://localhost:3001
Go to Dashboards → ObsStack folder
Select your application dashboard
See live metrics, traces, and logs!
Understanding the Workflow
┌─────────────────┐
│  Your App       │
│  (Flask/Django/ │
│   Express/etc)  │
└────────┬────────┘
         │
         │ 1. obs-stack detect
         ↓
┌─────────────────┐
│   Detection     │
│   Engine        │
└────────┬────────┘
         │
         │ 2. obs-stack instrument
         ↓
┌─────────────────┐
│ OpenTelemetry   │
│ Instrumentation │
└────────┬────────┘
         │
         │ 3. Telemetry Data
         ↓
┌─────────────────┐
│ OTEL Collector  │
└────────┬────────┘
         │
         ├──→ Prometheus (metrics)
         ├──→ Loki (logs)
         └──→ Tempo (traces)
         │
         ↓
┌─────────────────┐
│    Grafana      │
│  (Dashboards)   │
└─────────────────┘
Supported Frameworks
Framework	Language	Auto-Detect	Auto-Instrument	Dashboards
Flask	Python	✅	✅	✅
Django	Python	✅	✅	✅
FastAPI	Python	✅	✅	✅
Express	Node.js	✅	✅	✅
NestJS	Node.js	✅	🚧	🚧
Spring Boot	Java	✅	🚧	🚧
Common Use Cases
Case 1: Existing Application
You have a running Flask app in Docker:

bash
# 1. Initialize
obs-stack init

# 2. Start monitoring
obs-stack up

# 3. Instrument
obs-stack detect my-flask-container
obs-stack instrument my-flask-container

# 4. Restart your app
docker restart my-flask-container

# 5. View metrics
open http://localhost:3001
Case 2: New Application
Starting a new project:

bash
# 1. Create docker-compose.yml for your app
# 2. Initialize ObsStack
obs-stack init

# 3. Inject observability
obs-stack inject --all

# 4. Start everything
docker-compose up -d
obs-stack up

# Done! Monitoring is live
Case 3: Multiple Services
You have microservices:

bash
# Initialize once
obs-stack init

# Start observability
obs-stack up

# Instrument all services
obs-stack detect-all
obs-stack instrument-all

# Generate dashboards for each
obs-stack dashboard --all

# All services now monitored!
CLI Commands Reference
Setup Commands
bash
obs-stack init          # Initialize in project
obs-stack up            # Start observability stack
obs-stack down          # Stop observability stack
Detection Commands
bash
obs-stack detect <container>     # Detect framework
obs-stack detect-all             # Scan all containers
obs-stack validate <container>   # Detailed detection info
Instrumentation Commands
bash
obs-stack instrument <container>  # Add OpenTelemetry
obs-stack instrument-all          # Instrument all
obs-stack status [container]      # Check status
Integration Commands
bash
obs-stack inject [--service name]     # Inject into compose
obs-stack inject-running [container]  # Inject into running
Monitoring Commands
bash
obs-stack ps               # Show all containers
obs-stack logs [-f] [svc]  # View logs
obs-stack health           # Health check
obs-stack dashboard --all  # Generate dashboards
Configuration
System Config
Located in .obsstack/config.yml:

yaml
version: "3.0.0"

backend:
  network: "obs-stack-network"
  prometheus_port: 9090
  grafana_port: 3001

instrumentation:
  auto_detect: true
  auto_instrument: false
  frameworks:
    - flask
    - django
    - fastapi
    - express

monitoring:
  metrics_interval: 15s
  log_level: info
  retention:
    metrics: 15d
    logs: 7d
    traces: 24h
Environment Variables
bash
# Grafana
export GF_SECURITY_ADMIN_PASSWORD=your-password

# Prometheus
export PROMETHEUS_RETENTION=30d

# OTEL Collector
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
Troubleshooting
Services Not Starting
bash
# Check Docker
docker ps

# Check logs
obs-stack logs -f

# Restart
obs-stack down
obs-stack up
No Metrics Showing
Check instrumentation: obs-stack status
Restart container: docker restart <container>
Verify endpoint: curl http://localhost:4317
Check OTEL logs: obs-stack logs otel-collector
High Memory Usage
bash
# Check system requirements
obs-stack health

# Reduce retention
# Edit backend/prometheus/prometheus.yml
# Change: --storage.tsdb.retention.time=7d
Next Steps
Read Architecture Guide
Review Security Hardening
Check API Reference
See Examples
Join Community Discord
Getting Help
📖 Documentation
💬 Discord Community
🐛 GitHub Issues
📧 Email Support

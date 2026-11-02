# ObsStack V3 - Instant Observability for Any App

**Status:** 🚧 Alpha - Active Development

## What is ObsStack V3?

A plug-and-play observability solution that automatically detects your application framework and instruments it with monitoring - **zero code changes required**.

```bash
# That's it! Observability added.
curl -sSL https://get.obs-stack.io | bash
docker compose up -d
```

## Features

- 🔍 **Auto-Detection:** Identifies Flask, Django, Express, Spring Boot, and more
- 🎯 **Auto-Instrumentation:** Injects metrics, logs, and traces automatically
- 📊 **Auto-Dashboards:** Generates framework-specific Grafana dashboards
- 🚨 **Smart Alerts:** Pre-configured alerting with sensible defaults
- 🔒 **PII Redaction:** Automatically redacts sensitive data
- ⚡ **<5% Overhead:** Minimal performance impact

## Quick Start

```bash
# Install
obs-stack init

# Detect your app
obs-stack detect my-app-container

# Start monitoring
docker compose -f docker-compose.yml -f obs-stack.yml up -d
```

## Project Status

- [x] Sprint 0: Foundation (Week 1) - **IN PROGRESS**
- [ ] Sprint 1: Auto-Detection (Weeks 2-3)
- [ ] Sprint 2: Auto-Instrumentation (Weeks 4-5)
- [ ] Sprint 3: Configuration Engine (Week 6)
- [ ] Sprint 4: Docker Plugin (Week 7)
- [ ] Sprint 5: Testing & Docs (Week 8)
- [ ] Sprint 6: Kubernetes Support (Weeks 9-10)
- [ ] Sprint 7: Advanced Features (Week 11)
- [ ] Sprint 8: Release (Week 12)

## Development

```bash
# Setup
cd v3
python3.10 -m venv venv
source venv/bin/activate
pip install -e .

# Run CLI
obs-stack version
obs-stack detect <container-name>

# Run tests
pytest tests/
```

## Architecture

```
ObsStack V3
├── core/               # Detection & instrumentation engine
├── docker-plugin/      # Docker Compose integration
├── k8s-operator/       # Kubernetes operator
├── backend/            # Monitoring stack (Prometheus, Grafana, etc.)
└── cli/               # Command-line interface
```


# ObsStack V3 - Sprint 1 Complete ✅

Auto-detection engine for 6 frameworks with enhanced CLI.

## Quick Start
```bash
pip install -e .
obs-stack detect <container>
obs-stack detect-all
```

## Supported Frameworks
- Flask, Django, FastAPI (Python)
- Express, NestJS (Node.js)
- Spring Boot (Java)

## Status
Sprint 1: ✅ Complete (Detection Engine)
Sprint 2: 📅 Next (Auto-Instrumentation)



## Contributing

We're in active development! 

## License

MIT License - see [LICENSE](../LICENSE)

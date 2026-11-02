ObsStack V3 - Observability Backend
Complete monitoring infrastructure for ObsStack V3.

Components
Service	Purpose	Port	URL
Grafana	Dashboards & Visualization	3001	http://localhost:3001
Prometheus	Metrics Storage	9090	http://localhost:9090
Loki	Log Aggregation	3100	http://localhost:3100
Tempo	Distributed Tracing	3200	http://localhost:3200
OTEL Collector	Telemetry Receiver	4317/4318	-
AlertManager	Alert Routing	9093	http://localhost:9093
Quick Start
bash
# Start the observability stack
docker-compose up -d

# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Stop and remove data
docker-compose down -v
Access
Grafana
URL: http://localhost:3001
Username: admin
Password: obsstack
Prometheus
URL: http://localhost:9090
Query UI available
OpenTelemetry Collector
gRPC endpoint: localhost:4317
HTTP endpoint: localhost:4318
Data Flow
Application (instrumented)
    ↓
OpenTelemetry SDK
    ↓
OTLP Protocol (gRPC/HTTP)
    ↓
OpenTelemetry Collector
    ├─→ Prometheus (metrics)
    ├─→ Loki (logs)
    └─→ Tempo (traces)
    ↓
Grafana (visualization)
Storage
All data is persisted in Docker volumes:

prometheus_data - Metrics (15 days retention)
grafana_data - Dashboards and config
loki_data - Logs
tempo_data - Traces
Resource Usage
Expected resource consumption:

CPU: ~500m (0.5 cores)
Memory: ~2GB
Disk: ~10GB (with 15 day retention)
Configuration
Prometheus
Config: prometheus/prometheus.yml
Scrape interval: 15s
Retention: 15 days
OpenTelemetry Collector
Config: otel-collector/config.yml
Batch size: 1024
Memory limit: 512MB
Loki
Config: loki/config.yml
Retention: 7 days
Max ingestion: 10MB/s
Tempo
Config: tempo/config.yml
Retention: 1 hour
Storage: Local filesystem
Troubleshooting
Service not starting
bash
# Check logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
Out of memory
bash
# Check resource usage
docker stats

# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory
No data in Grafana
Check OTEL Collector is receiving data: http://localhost:8888/metrics
Check Prometheus targets: http://localhost:9090/targets
Verify application is sending telemetry
Ports already in use
bash
# Find process using port
lsof -i :<port>

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
Security
⚠️ This is a development setup. For production:

Change Grafana admin password
Enable authentication on all services
Use TLS/SSL certificates
Restrict network access
Enable authentication in OTEL Collector
Use secrets management
Monitoring the Monitor
The observability stack monitors itself:

Prometheus scrapes its own metrics
OTEL Collector exports self-metrics
Grafana, Loki, Tempo metrics available
Backup
bash
# Backup all data volumes
docker run --rm \
  -v obs-stack_prometheus_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/prometheus-backup.tar.gz /data

# Restore
docker run --rm \
  -v obs-stack_prometheus_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/prometheus-backup.tar.gz -C /
Upgrade
bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate
Integration with ObsStack CLI
This backend is automatically started when you run:

bash
obs-stack up
And stopped with:

bash
obs-stack down

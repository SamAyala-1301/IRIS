
# 🔭 Observability Stack v2: Production-Grade SRE Platform

**Tagline:**  
_A modern, end-to-end observability platform: metrics, logs, traces, SLOs, alerting, and auto-remediation for distributed microservices._  
**Keywords:** observability, SRE, Prometheus, Grafana, distributed tracing, microservices, alerting, OpenTelemetry, DevOps, chaos engineering

---

## 🚀 Project Overview
This project delivers a **production-grade observability stack** for microservices, integrating the three pillars of observability (metrics, logs, traces) with robust alerting, SLO monitoring, distributed tracing, caching, and automated incident remediation.  
**Ideal for:** SRE/DevOps portfolios, learning cloud-native monitoring, or as a blueprint for real-world distributed systems.

---

## ✨ Key Features
- **Full Observability:** Metrics, logs, and distributed traces across 4 microservices
- **Real Microservices:** Auth, Payment, Inventory, and Worker, with Nginx API Gateway
- **Advanced Caching:** Redis with >70% hit rate, cache invalidation patterns
- **Asynchronous Processing:** RabbitMQ message queue, async notification worker
- **Distributed Tracing:** OpenTelemetry + Tempo, full request flow visualization
- **SLO Monitoring:** Error budgets, burn rates, and alerting
- **Automated Remediation:** Self-healing containers via alert bot
- **Business Metrics:** Revenue, conversion, active users
- **Production Patterns:** Rate limiting, JWT, health checks, structured logging

---

## 🏗️ Architecture
```
                        Nginx API Gateway (Port 80)
                        Rate Limiting: 10 req/sec
                                  |
           +──────────────────────┼──────────────────────+
           |                      |                      |
     ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
     │   Auth    │         │  Payment  │         │ Inventory │
     │  Service  │         │  Service  │         │  Service  │
     └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
           │                     │                      │
           ├─────────────────────┴──────────────────────┤
           │                                             │
     ┌─────▼──────┐                              ┌──────▼──────┐
     │   Redis    │◄─────── Cache ──────────────►│ PostgreSQL  │
     └────────────┘                               └─────────────┘
           │
     ┌─────▼──────┐         ┌──────────────┐
     │ RabbitMQ   │────────►│ Notification │
     └────────────┘         │   Worker     │
                            └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│        Observability Stack (Prometheus, Grafana, etc.)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer           | Technology                | Purpose                                  | Version    |
|-----------------|--------------------------|------------------------------------------|------------|
| API Gateway     | Nginx                    | Rate limiting, routing, load balancing   | Alpine     |
| Auth Service    | Flask + JWT              | User authentication, session management  | Python 3.10|
| Payment Service | Flask + OpenTelemetry    | Payment processing, tracing              | Python 3.10|
| Inventory       | Flask + Redis            | Product catalog, stock mgmt, caching     | Python 3.10|
| Worker          | Python + Pika            | Async notification processing            | Python 3.10|
| Database        | PostgreSQL               | Persistent data storage                  | 15-Alpine  |
| Cache           | Redis                    | Session/product cache                    | 7-Alpine   |
| Message Queue   | RabbitMQ                 | Async event processing                   | 3-Mgmt     |
| Metrics         | Prometheus               | Metrics & alerting                       | Latest     |
| Logs            | Loki + Promtail          | Centralized log aggregation              | 2.9.0      |
| Traces          | Tempo + OpenTelemetry    | Distributed tracing                      | 2.3.0      |
| Visualization   | Grafana                  | Dashboards                               | Latest     |
| Alerting        | Alertmanager             | Alert routing, grouping                  | Latest     |
| Automation      | Python + Docker SDK      | Self-healing incident response           | Latest     |
| Exporters       | Node, cAdvisor, Redis    | Infra metrics                            | Latest     |

---

## ⚡ Quick Start
**Prerequisites**
- Docker 20.10+ with Compose V2
- 4GB+ RAM (8GB recommended), 10GB disk, free ports: 80, 3000, 3100, 3200, 9090, 9093, 15672, 8000-8003, etc.

**Installation**
```bash
# 1. Clone the repository
git clone https://github.com/SamAyala-1301/Observability-Stack-Refined.git
cd Observability-Stack-Refined

# 2. Start the stack
docker compose up -d --build

# 3. Wait for initialization
echo "Waiting for services to start..." && sleep 60

# 4. Validate setup
chmod +x scripts/validate-v2.sh
./scripts/validate-v2.sh
```

**Access the Stack**
| Service         | URL                        | Credentials       | Description                    |
|-----------------|---------------------------|-------------------|--------------------------------|
| API Gateway     | http://localhost          | -                 | Rate-limited entry point       |
| Grafana         | http://localhost:3000     | admin / admin     | Dashboards & visualization     |
| Prometheus      | http://localhost:9090     | -                 | Metrics DB & queries           |
| Alertmanager    | http://localhost:9093     | -                 | Alert management               |
| RabbitMQ UI     | http://localhost:15672    | admin / admin     | Message queue management       |
| Tempo           | http://localhost:3200     | -                 | Trace storage (via Grafana)    |

---

## 📊 Grafana Dashboards
- **Master Overview:** Real-time health, error rates, cache hit rate, quick links
- **SLO Dashboard:** Service Level Objectives, error budgets, burn rates
- **Business Metrics:** Revenue, conversions, active users, top products
- **Service Map:** Microservice topology, request flow, latency
- **Infrastructure:** CPU/memory/queue depth, DB/Redis/RabbitMQ stats

**Access:**  
Visit [http://localhost:3000](http://localhost:3000) (admin/admin) → Dashboards

---

## 🧪 Testing & Chaos Engineering
- **End-to-End Test:**  
  ```bash
  ./scripts/validate-v2.sh
  ```
- **Manual API Flow:** Register, login, charge, get products, reserve stock (see script for curl commands)
- **Load Test:**  
  ```bash
  ./scripts/load_test.sh
  ```
- **Chaos Engineering:**  
  ```bash
  ./scripts/chaos.sh
  ```
  Randomly kills services; observe recovery, SLO burn, and alerting in Grafana.

---

## 🔍 Distributed Tracing
- **End-to-End Traces:** OpenTelemetry auto-instrumentation, Tempo backend
- **View Traces:**  
  - Grafana → Explore (select Tempo) → Search traces → Waterfall view
- **Trace Example:**  
  See full request breakdown: API Gateway → Auth → Redis → Payment → DB → RabbitMQ → Notification

---

## 🚨 Alerting System Overview
- **Pre-configured Alerts:** High error rate, high latency (P95), SLO burn, error budget exhausted
- **Alert Flow:**  
  Prometheus → Alertmanager → Webhook → Alert Bot → Auto-remediation (container restart) → Recovery
- **Test Alerts:**  
  - Generate errors:  
    ```bash
    for i in {1..20}; do curl http://localhost:8000/error; sleep 0.3; done
    ```
  - Overload:  
    ```bash
    for i in {1..100}; do curl -X POST http://localhost:8000/transactions/create & done
    ```
- **Monitor:** View active alerts in Prometheus/Alertmanager UI, follow Alert Bot logs.

---

<details>
<summary>📚 <b>Advanced: Metrics, Queries, Config, Troubleshooting</b></summary>

### 📈 Key Metrics & PromQL Queries

**Golden Signals:**
- Request Rate:  
  `rate(flask_http_request_total[5m])`
- Error Rate (%):  
  `sum(rate(flask_http_request_total{status=~"5.."}[5m])) / sum(rate(flask_http_request_total[5m])) * 100`
- Latency (P95):  
  `histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))`
- Cache Hit Rate:  
  `rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100`

**Business Metrics:**
- Revenue: `business_revenue_total_dollars`
- Active Users: `auth_active_sessions`
- Payment Success Rate:  
  `rate(payment_transactions_total{status="success"}[5m]) / rate(payment_transactions_total[5m]) * 100`

**SLO/SLI:**
- Availability:  
  `auth:availability:ratio = sum(rate(flask_http_request_total{job="auth_service",status=~"2.."}[5m])) / sum(rate(flask_http_request_total{job="auth_service"}[5m]))`
- Error Budget Remaining:  
  `(1 - 0.999) - (1 - avg_over_time(auth:availability:ratio[30d]))`
- Burn Rate:  
  `(1 - avg_over_time(auth:availability:ratio[1h])) / (1 - 0.999)`

**Advanced Queries:**  
Top 5 slowest endpoints, memory usage per service, DB pool utilization, RabbitMQ/Redis stats, etc.

---

### 🛠️ Configuration & Customization
- **Alert Thresholds:** Edit `alert_rules.yml`
- **SLO Targets:** Edit `prometheus/recording_rules.yml`
- **Cache TTL:** Change `CACHE_TTL` in `api/app.py`
- **Debug Logging:** `docker logs -f <service>`
- **Grafana Explore:** Query logs/errors via Loki datasource

---

### 🚧 Troubleshooting
- **Containers fail:** `docker logs <service>`, `docker compose ps`, restart as needed
- **Prometheus not scraping:** Check `/metrics` endpoint, targets, config
- **No traces:** Check OTEL collector logs, Tempo, service env
- **Alert bot not working:** Check webhook, Docker socket, Alertmanager config
- **RabbitMQ/Redis issues:** Check health, logs, restart if needed
- **Grafana dashboards missing:** Check datasources, provisioning, restart Grafana
</details>

---

## 💼 Resume Highlights
- **Built a production-grade distributed observability platform** with 4 microservices, implementing metrics, logs, and traces.
- **Integrated Prometheus, Loki, Tempo, Redis, RabbitMQ, and Nginx** for a real-world, cloud-native stack.
- **Achieved full distributed tracing** with OpenTelemetry and automated alerting/remediation.
- **Comprehensive Grafana dashboards** tracking SLOs, business metrics, and infrastructure.
- **Handles 1000+ req/min with sub-200ms P95 latency** and 99.9% availability targets.

---

## 🤝 Contributing
Contributions welcome!  
**Ideas:**  
- New alert rules (CPU/memory/disk/network)
- More dashboards (DB perf, network, security)
- Enhanced alert bot (deduplication, escalation, Slack/PagerDuty)
- More tests, chaos scenarios, multi-environment support
- Kubernetes/Helm, Terraform, CI/CD, cloud integrations

---

## 📄 License
MIT License – see [LICENSE](LICENSE) for details.

---

## 👤 Author
**Naga Sowmya Ganti**  
GitHub: [@SamAyala-1301](https://github.com/SamAyala-1301)

---

## 🙏 Acknowledgments
Thanks to the open-source community:
- Prometheus, Grafana, Loki, Tempo, OpenTelemetry
- PostgreSQL, Redis, RabbitMQ, Nginx, Flask, Docker

**Resources:**  
- Prometheus Best Practices  
- OpenTelemetry Python Docs  
- Grafana Dashboard Guides  
- Google SRE Book (free)  
- Site Reliability Engineering Workbook  
- Prometheus Alerting Best Practices  

⭐ _If you found this helpful, please star the repository!_

---

## 🗺️ Roadmap
**Planned for v3:**
- Plug-and-play install for any project
- Multi-language auto-instrumentation (Node.js, Go, Java, Python)
- Helm charts for Kubernetes
- ML-based anomaly detection, predictive alerting
- Cloud metric correlation (AWS/GCP/Azure)
- Cost monitoring dashboards

**Future:**
- Security dashboard, compliance/SLA reporting
- A/B testing metrics
- Mobile app for on-call engineers
- AI-powered root cause analysis
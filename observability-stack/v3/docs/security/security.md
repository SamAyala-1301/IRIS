Security Hardening Guide
Overview
ObsStack V3 includes several security features. This guide shows how to harden your deployment for production.

Quick Security Checklist
 Change default Grafana password
 Enable authentication on all services
 Use TLS/SSL certificates
 Restrict network access
 Enable audit logging
 Regular security updates
 Use secrets management
 Enable firewall rules
Default Credentials
⚠️ CHANGE THESE IMMEDIATELY IN PRODUCTION

Service	Username	Default Password
Grafana	admin	obsstack
1. Change Grafana Password
bash
# Method 1: Environment variable
export GF_SECURITY_ADMIN_PASSWORD='your-secure-password'
obs-stack up

# Method 2: Grafana CLI
docker exec obs-stack-grafana grafana-cli admin reset-admin-password 'your-secure-password'
2. Enable Authentication
Prometheus Basic Auth
Create prometheus/web.yml:

yaml
basic_auth_users:
  admin: '$2y$10$...'  # Generate with htpasswd
Update docker-compose.yml:

yaml
prometheus:
  command:
    - '--web.config.file=/etc/prometheus/web.yml'
  volumes:
    - ./prometheus/web.yml:/etc/prometheus/web.yml
OTEL Collector Authentication
Update otel-collector/config.yml:

yaml
extensions:
  basicauth:
    htpasswd:
      file: /etc/otel/users.htpasswd

receivers:
  otlp:
    protocols:
      grpc:
        auth:
          authenticator: basicauth
3. TLS/SSL Configuration
Generate Self-Signed Certificates (Dev)
bash
mkdir -p backend/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout backend/ssl/obsstack.key \
  -out backend/ssl/obsstack.crt \
  -subj "/CN=localhost"
Configure Grafana with TLS
yaml
grafana:
  environment:
    - GF_SERVER_PROTOCOL=https
    - GF_SERVER_CERT_FILE=/etc/ssl/obsstack.crt
    - GF_SERVER_CERT_KEY=/etc/ssl/obsstack.key
  volumes:
    - ./ssl/obsstack.crt:/etc/ssl/obsstack.crt
    - ./ssl/obsstack.key:/etc/ssl/obsstack.key
  ports:
    - "443:3000"
4. Network Security
Restrict to Internal Network Only
yaml
services:
  prometheus:
    ports:
      - "127.0.0.1:9090:9090"  # Localhost only
  
  grafana:
    ports:
      - "0.0.0.0:3001:3000"  # Public (behind reverse proxy)
Use Docker Networks
All ObsStack services use isolated network:

yaml
networks:
  obs-stack:
    external: true
    driver: bridge
5. Secrets Management
Use Docker Secrets (Swarm)
yaml
secrets:
  grafana_password:
    file: ./secrets/grafana_password.txt

services:
  grafana:
    secrets:
      - grafana_password
    environment:
      - GF_SECURITY_ADMIN_PASSWORD__FILE=/run/secrets/grafana_password
Use Environment Files
bash
# Create .env file
echo "GF_SECURITY_ADMIN_PASSWORD=secure-password" > .env

# Load in compose
docker-compose --env-file .env up
6. Audit Logging
Enable Grafana Audit Logs
yaml
grafana:
  environment:
    - GF_LOG_MODE=console file
    - GF_LOG_LEVEL=info
Prometheus Audit Logs
yaml
prometheus:
  command:
    - '--log.level=info'
    - '--log.format=json'
7. Rate Limiting
OTEL Collector
yaml
processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
8. Security Headers
Nginx Reverse Proxy Example
nginx
server {
    listen 443 ssl http2;
    server_name obsstack.example.com;

    ssl_certificate /etc/ssl/obsstack.crt;
    ssl_certificate_key /etc/ssl/obsstack.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
9. Regular Updates
bash
# Update ObsStack
cd v3
git pull
pip install -e . --upgrade

# Update backend images
cd backend
docker-compose pull
docker-compose up -d
10. Firewall Rules
UFW (Ubuntu)
bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 443/tcp   # HTTPS
ufw deny 9090/tcp   # Block Prometheus externally
ufw deny 3100/tcp   # Block Loki externally

ufw enable
iptables
bash
# Allow Grafana
iptables -A INPUT -p tcp --dport 3001 -j ACCEPT

# Block direct access to backends
iptables -A INPUT -p tcp --dport 9090 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 9090 -j DROP
Security Monitoring
Monitor Failed Login Attempts
promql
# Grafana failed logins
increase(grafana_api_login_post_total{status="failed"}[5m]) > 5
Alert on Unauthorized Access
yaml
- alert: UnauthorizedAccess
  expr: rate(prometheus_http_requests_total{code="401"}[5m]) > 0
  annotations:
    summary: "Unauthorized access attempts detected"
Compliance
GDPR Considerations
PII redaction enabled by default
Data retention policies configured
User data export available
Right to deletion supported
SOC 2 Recommendations
Enable audit logging
Implement access controls
Regular security updates
Incident response plan
Vulnerability Scanning
bash
# Scan Docker images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image obs-stack-grafana

# Scan Python dependencies
pip install safety
safety check
Incident Response
Isolate affected containers
Review audit logs
Rotate credentials
Apply security patches
Document and report
Resources
Grafana Security
Prometheus Security
Docker Security
OWASP Top 10

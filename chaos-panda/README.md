
# ChaosPanda 🐼

Kubernetes chaos engine that injects failures, measures recovery (TTD/TTR), and emits structured incident data to the IRIS Incident Intelligence Ecosystem.

---

## 🔗 IRIS Integration

ChaosPanda is the **event producer** in the IRIS ecosystem.

After each experiment, it emits a structured `IrisEvent` to a shared store (`~/.iris/iris.db`). This allows downstream tools like RCA-GPT, CIIA, and the Observability Stack to consume the same incident context.

### Data Flow

ChaosPanda → emits IrisEvent<br>
↓<br>
IRIS store (`~/.iris/iris.db`)<br>
↓<br>
RCA-GPT → classifies incident<br>
↓<br>
CIIA → enriches tickets<br>
↓<br>
Obs Stack → visualizes TTD/TTR + trends

### Example Event

```python
IrisEvent(
    source      = "chaospanda",
    event_type  = "pod_kill",
    severity    = "degraded",
    ttd_seconds = 1.03,
    ttr_seconds = 7.09,
    metadata    = {
        "deployment": "chaos-target",
        "namespace" : "default",
        "pod_killed": "chaos-target-abc123",
    }
)
```

> If IRIS-Core is not installed, ChaosPanda continues to run normally (graceful degradation).

---

## 🚀 What ChaosPanda Does

- Connects to any Kubernetes cluster via kubeconfig
- Kills pods in a target deployment (fault injection)
- Measures **TTD (Time to Detect)** and **TTR (Time to Recover)**
- Stores local experiment history
- Emits structured events for cross-tool intelligence

---

## 📦 Legacy: Sprint 1 (AWS EKS Setup)

### What We Built
- **VPC Infrastructure**: Custom VPC with public/private subnets across 2 AZs
- **EKS Cluster**: Kubernetes 1.28 with 2 t3.medium nodes
- **Sample Microservices**: 
  - Frontend (2 replicas, LoadBalancer)
  - Backend API (3 replicas, ClusterIP)
  - Database simulator (1 replica)
- **Monitoring**: CloudWatch Container Insights + Custom Dashboard

### Architecture
```
Internet
    ↓
LoadBalancer → Frontend Pods (x2)
                    ↓
            Backend API Pods (x3)
                    ↓
              Database Pod (x1)
```

### Quick Commands
```bash
# Check cluster status
kubectl get nodes

# Check applications
kubectl get all -n chaospanda-apps

# View logs
kubectl logs -n chaospanda-apps -l app=frontend --tail=50

# Get frontend URL
kubectl get svc frontend -n chaospanda-apps

# Run verification
./scripts/verify-sprint1.sh
```

### AWS Resources Created
- 1 VPC with 4 subnets (2 public, 2 private)
- 1 Internet Gateway
- 1 NAT Gateway
- 1 EKS Cluster
- 1 EKS Node Group (2 nodes)
- Security Groups, Route Tables, IAM Roles
- CloudWatch Log Groups

### Costs (Estimated)
- EKS Control Plane: ~$73/month (NOT free tier)
- t3.medium nodes: ~$60/month for 2 nodes
- NAT Gateway: ~$32/month
- **Total: ~$165/month**

⚠️ **Important**: This exceeds free tier. Stop resources when not in use!

### Next: Sprint 2
- Elasticsearch + Kibana for centralized logging
- Fluent Bit log aggregation
- Enhanced CloudWatch dashboards
- Custom metrics and alerts

## Project Structure
```
ChaosPanda/
├── terraform/           # Infrastructure as Code
│   ├── vpc/            # VPC module
│   ├── eks/            # EKS module
│   └── main.tf         # Root config
├── kubernetes/          # K8s manifests
│   └── apps/           # Application deployments
├── scripts/            # Automation scripts
└── docs/               # Documentation
```

## Useful Links
- [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/)
- [EKS Console](https://console.aws.amazon.com/eks/)
- [VPC Console](https://console.aws.amazon.com/vpc/)


# ChaosPanda 🐼💥

Lightweight chaos engineering platform for AWS Free Tier.

## Sprint 1: ✅ COMPLETE

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


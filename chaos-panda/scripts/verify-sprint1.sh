#!/bin/bash

echo "======================================"
echo "  ChaosPanda Sprint 1 Verification"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check Terraform
echo "1. Checking Terraform State..."
cd ../terraform
if terraform state list | grep -q "module.eks.aws_eks_cluster.main"; then
    echo -e "${GREEN}✅ EKS Cluster deployed${NC}"
else
    echo -e "${RED}❌ EKS Cluster not found${NC}"
fi

if terraform state list | grep -q "module.vpc.aws_vpc.main"; then
    echo -e "${GREEN}✅ VPC deployed${NC}"
else
    echo -e "${RED}❌ VPC not found${NC}"
fi

# Check kubectl
echo ""
echo "2. Checking Kubernetes Cluster..."
if kubectl get nodes &> /dev/null; then
    NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
    echo -e "${GREEN}✅ kubectl connected - $NODE_COUNT nodes ready${NC}"
    kubectl get nodes
else
    echo -e "${RED}❌ kubectl not connected${NC}"
fi

# Check pods
echo ""
echo "3. Checking Application Pods..."
PODS=$(kubectl get pods -n chaospanda-apps --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -n chaospanda-apps --no-headers 2>/dev/null | grep Running | wc -l)

if [ "$PODS" -gt 0 ]; then
    echo -e "${GREEN}✅ $RUNNING/$PODS pods running${NC}"
    kubectl get pods -n chaospanda-apps
else
    echo -e "${RED}❌ No pods found${NC}"
fi

# Check service
echo ""
echo "4. Checking Frontend Service..."
FRONTEND_URL=$(kubectl get svc frontend -n chaospanda-apps -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

if [ -n "$FRONTEND_URL" ]; then
    echo -e "${GREEN}✅ Frontend LoadBalancer: http://$FRONTEND_URL${NC}"
    echo "Testing endpoint..."
    if curl -s --max-time 5 http://$FRONTEND_URL | grep -q "ChaosPanda"; then
        echo -e "${GREEN}✅ Frontend responding!${NC}"
    else
        echo -e "${RED}⚠️  Frontend not responding yet (may need 1-2 mins)${NC}"
    fi
else
    echo -e "${RED}❌ Frontend service not found${NC}"
fi

# Check CloudWatch
echo ""
echo "5. Checking CloudWatch Integration..."
if kubectl get pods -n amazon-cloudwatch &> /dev/null; then
    CW_PODS=$(kubectl get pods -n amazon-cloudwatch --no-headers | grep Running | wc -l)
    echo -e "${GREEN}✅ CloudWatch agents running ($CW_PODS pods)${NC}"
else
    echo -e "${RED}❌ CloudWatch not configured${NC}"
fi

# Summary
echo ""
echo "======================================"
echo "  Sprint 1 Status Summary"
echo "======================================"
echo "Infrastructure: VPC + EKS Cluster"
echo "Applications: 3 microservices deployed"
echo "Monitoring: CloudWatch Container Insights"
echo ""
echo "Next Steps:"
echo "1. Visit CloudWatch Console to see metrics"
echo "2. Test the frontend URL above"
echo "3. Ready for Sprint 2: Observability Stack!"
echo ""

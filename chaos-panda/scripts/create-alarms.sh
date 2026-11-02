#!/bin/bash

CLUSTER_NAME=$(cd ../terraform && terraform output -raw eks_cluster_name)
REGION=us-east-1

# Create SNS topic for alerts
SNS_TOPIC_ARN=$(aws sns create-topic --name chaospanda-alerts --region $REGION --output text --query 'TopicArn')

echo "SNS Topic created: $SNS_TOPIC_ARN"
echo "Enter your email for alerts:"
read EMAIL

# Subscribe to SNS topic
aws sns subscribe \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol email \
  --notification-endpoint $EMAIL \
  --region $REGION

echo "⚠️  Check your email and confirm the subscription!"
echo ""

# Create high CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ChaosPanda-HighCPU \
  --alarm-description "Alert when pod CPU > 80%" \
  --metric-name pod_cpu_utilization \
  --namespace ContainerInsights \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC_ARN \
  --region $REGION

# Create pod restart alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ChaosPanda-PodRestarts \
  --alarm-description "Alert when pods restart frequently" \
  --metric-name pod_number_of_container_restarts \
  --namespace ContainerInsights \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions $SNS_TOPIC_ARN \
  --region $REGION

echo "✅ CloudWatch Alarms created!"

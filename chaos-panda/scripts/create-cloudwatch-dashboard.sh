#!/bin/bash

CLUSTER_NAME=$(cd ../terraform && terraform output -raw eks_cluster_name)
REGION=us-east-1

aws cloudwatch put-dashboard --dashboard-name ChaosPanda-Overview --region $REGION --dashboard-body '{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/EKS", "cluster_failed_node_count", { "stat": "Average" } ],
          [ ".", "cluster_node_count", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "'"$REGION"'",
        "title": "EKS Cluster Nodes",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "ContainerInsights", "pod_cpu_utilization", { "stat": "Average" } ],
          [ ".", "pod_memory_utilization", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "'"$REGION"'",
        "title": "Pod Resource Utilization",
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100
          }
        }
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '\''/aws/containerinsights/'"$CLUSTER_NAME"'/application'\'' | fields @timestamp, log | sort @timestamp desc | limit 20",
        "region": "'"$REGION"'",
        "title": "Recent Application Logs",
        "stacked": false
      }
    }
  ]
}'

echo "✅ CloudWatch Dashboard created: ChaosPanda-Overview"
echo "View at: https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=ChaosPanda-Overview"

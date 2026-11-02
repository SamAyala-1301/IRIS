"""Auto-generate Grafana dashboards for detected frameworks."""
import json
from typing import Dict, List
from pathlib import Path

class DashboardGenerator:
    """Generate framework-specific Grafana dashboards."""
    
    def __init__(self):
        self.dashboard_templates = {
            'flask': self._flask_template,
            'django': self._django_template,
            'fastapi': self._fastapi_template,
            'express': self._express_template,
        }
    
    def generate_dashboard(self, framework: str, service_name: str) -> Dict:
        """
        Generate a dashboard for a specific framework and service.
        
        Args:
            framework: Framework name (flask, django, etc.)
            service_name: Name of the service
        
        Returns:
            Dashboard JSON dict
        """
        template_func = self.dashboard_templates.get(framework.lower())
        if not template_func:
            return self._generic_template(service_name)
        
        return template_func(service_name)
    
    def save_dashboard(self, dashboard: Dict, output_path: str):
        """Save dashboard JSON to file."""
        with open(output_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
    
    def _flask_template(self, service_name: str) -> Dict:
        """Flask dashboard template."""
        return {
            "dashboard": {
                "title": f"Flask - {service_name}",
                "tags": ["obsstack", "flask", service_name],
                "timezone": "browser",
                "refresh": "10s",
                "panels": [
                    self._request_rate_panel(0, 0, "flask", service_name),
                    self._response_time_panel(12, 0, "flask", service_name),
                    self._error_rate_panel(0, 8, "flask", service_name),
                    self._memory_panel(12, 8, "python", service_name),
                ]
            }
        }
    
    def _django_template(self, service_name: str) -> Dict:
        """Django dashboard template."""
        return {
            "dashboard": {
                "title": f"Django - {service_name}",
                "tags": ["obsstack", "django", service_name],
                "timezone": "browser",
                "refresh": "10s",
                "panels": [
                    self._request_rate_panel(0, 0, "django", service_name),
                    self._response_time_panel(12, 0, "django", service_name),
                    self._error_rate_panel(0, 8, "django", service_name),
                    self._db_query_panel(12, 8, service_name),
                ]
            }
        }
    
    def _fastapi_template(self, service_name: str) -> Dict:
        """FastAPI dashboard template."""
        return {
            "dashboard": {
                "title": f"FastAPI - {service_name}",
                "tags": ["obsstack", "fastapi", service_name],
                "timezone": "browser",
                "refresh": "10s",
                "panels": [
                    self._request_rate_panel(0, 0, "fastapi", service_name),
                    self._response_time_panel(12, 0, "fastapi", service_name),
                    self._error_rate_panel(0, 8, "fastapi", service_name),
                    self._async_tasks_panel(12, 8, service_name),
                ]
            }
        }
    
    def _express_template(self, service_name: str) -> Dict:
        """Express.js dashboard template."""
        return {
            "dashboard": {
                "title": f"Express - {service_name}",
                "tags": ["obsstack", "express", service_name],
                "timezone": "browser",
                "refresh": "10s",
                "panels": [
                    self._request_rate_panel(0, 0, "express", service_name),
                    self._response_time_panel(12, 0, "express", service_name),
                    self._event_loop_panel(0, 8, service_name),
                    self._heap_memory_panel(12, 8, service_name),
                ]
            }
        }
    
    def _generic_template(self, service_name: str) -> Dict:
        """Generic dashboard for unknown frameworks."""
        return {
            "dashboard": {
                "title": f"Generic - {service_name}",
                "tags": ["obsstack", service_name],
                "timezone": "browser",
                "refresh": "10s",
                "panels": [
                    self._generic_metrics_panel(0, 0, service_name),
                ]
            }
        }
    
    # Panel generators
    def _request_rate_panel(self, x: int, y: int, framework: str, service: str) -> Dict:
        """Generate request rate panel."""
        metric_map = {
            'flask': 'flask_http_request_total',
            'django': 'django_http_requests_total',
            'fastapi': 'fastapi_requests_total',
            'express': 'http_request_duration_ms_count',
        }
        metric = metric_map.get(framework, 'http_requests_total')
        
        return {
            "id": 1,
            "title": "Request Rate",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'rate({metric}{{service=~"{service}"}}[5m])',
                "legendFormat": "{{method}} {{path}}"
            }],
            "yaxes": [
                {"format": "reqps", "label": "Requests/sec"},
                {"format": "short"}
            ]
        }
    
    def _response_time_panel(self, x: int, y: int, framework: str, service: str) -> Dict:
        """Generate response time panel."""
        return {
            "id": 2,
            "title": "Response Time (p95)",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service=~"{service}"}}[5m]))',
                "legendFormat": "p95"
            }],
            "yaxes": [
                {"format": "s", "label": "Duration"},
                {"format": "short"}
            ]
        }
    
    def _error_rate_panel(self, x: int, y: int, framework: str, service: str) -> Dict:
        """Generate error rate panel."""
        return {
            "id": 3,
            "title": "Error Rate",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'rate(http_requests_total{{service=~"{service}",status=~"5.."}}[5m])',
                "legendFormat": "{{status}}"
            }],
            "yaxes": [
                {"format": "reqps", "label": "Errors/sec"},
                {"format": "short"}
            ]
        }
    
    def _memory_panel(self, x: int, y: int, lang: str, service: str) -> Dict:
        """Generate memory usage panel."""
        metric = "process_resident_memory_bytes" if lang == "python" else "nodejs_heap_size_used_bytes"
        return {
            "id": 4,
            "title": "Memory Usage",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'{metric}{{service=~"{service}"}}',
                "legendFormat": "Memory"
            }],
            "yaxes": [
                {"format": "bytes"},
                {"format": "short"}
            ]
        }
    
    def _event_loop_panel(self, x: int, y: int, service: str) -> Dict:
        """Generate event loop lag panel (Node.js)."""
        return {
            "id": 5,
            "title": "Event Loop Lag",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'nodejs_eventloop_lag_seconds{{service=~"{service}"}}',
                "legendFormat": "Lag"
            }],
            "yaxes": [
                {"format": "s"},
                {"format": "short"}
            ]
        }
    
    def _heap_memory_panel(self, x: int, y: int, service: str) -> Dict:
        """Generate heap memory panel (Node.js)."""
        return {
            "id": 6,
            "title": "Heap Memory",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": f'nodejs_heap_size_used_bytes{{service=~"{service}"}}',
                    "legendFormat": "Used"
                },
                {
                    "expr": f'nodejs_heap_size_total_bytes{{service=~"{service}"}}',
                    "legendFormat": "Total"
                }
            ],
            "yaxes": [
                {"format": "bytes"},
                {"format": "short"}
            ]
        }
    
    def _db_query_panel(self, x: int, y: int, service: str) -> Dict:
        """Generate database query panel (Django)."""
        return {
            "id": 7,
            "title": "Database Queries",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'rate(django_db_query_duration_seconds_count{{service=~"{service}"}}[5m])',
                "legendFormat": "Queries/sec"
            }]
        }
    
    def _async_tasks_panel(self, x: int, y: int, service: str) -> Dict:
        """Generate async tasks panel (FastAPI)."""
        return {
            "id": 8,
            "title": "Async Tasks",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 12, "h": 8},
            "targets": [{
                "expr": f'fastapi_tasks_active{{service=~"{service}"}}',
                "legendFormat": "Active Tasks"
            }]
        }
    
    def _generic_metrics_panel(self, x: int, y: int, service: str) -> Dict:
        """Generate generic metrics panel."""
        return {
            "id": 1,
            "title": "Service Metrics",
            "type": "graph",
            "gridPos": {"x": x, "y": y, "w": 24, "h": 12},
            "targets": [{
                "expr": f'{{service=~"{service}"}}',
                "legendFormat": "{{__name__}}"
            }]
        }
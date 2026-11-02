"""Generate obs-stack.yml for application integration."""
import yaml
from typing import Dict, List, Optional
from pathlib import Path

class ComposeGenerator:
    """Generate Docker Compose configuration for ObsStack integration."""
    
    def __init__(self, backend_path: str = "backend"):
        self.backend_path = backend_path
        self.obs_stack_network = "obs-stack-network"
    
    def generate_integration_compose(
        self, 
        app_services: List[str],
        existing_compose_path: Optional[str] = None
    ) -> Dict:
        """
        Generate obs-stack.yml that integrates with existing app.
        
        Args:
            app_services: List of application service names to instrument
            existing_compose_path: Path to existing docker-compose.yml
        
        Returns:
            Dict representing the integration compose file
        """
        compose = {
            'version': '3.8',
            'networks': {
                self.obs_stack_network: {
                    'external': True,
                    'name': self.obs_stack_network
                }
            },
            'services': {}
        }
        
        # Add integration for each app service
        for service_name in app_services:
            compose['services'][service_name] = self._generate_service_integration(service_name)
        
        return compose
    
    def _generate_service_integration(self, service_name: str) -> Dict:
        """Generate integration config for a single service."""
        return {
            'networks': [self.obs_stack_network],
            'environment': [
                'OTEL_EXPORTER_OTLP_ENDPOINT=http://obs-stack-otel-collector:4317',
                'OTEL_SERVICE_NAME=${SERVICE_NAME:-' + service_name + '}',
                'OTEL_RESOURCE_ATTRIBUTES=service.name=${SERVICE_NAME:-' + service_name + '}',
                'OTEL_TRACES_EXPORTER=otlp',
                'OTEL_METRICS_EXPORTER=otlp',
                'OTEL_LOGS_EXPORTER=otlp',
            ],
            'labels': [
                'obs_stack.enabled=true',
                f'obs_stack.service={service_name}',
                'obs_stack.version=3.0.0',
            ]
        }
    
    def save_compose_file(self, compose_dict: Dict, output_path: str = "obs-stack.yml"):
        """Save compose configuration to file."""
        with open(output_path, 'w') as f:
            yaml.dump(compose_dict, f, default_flow_style=False, sort_keys=False)
    
    def load_existing_compose(self, compose_path: str) -> Dict:
        """Load existing docker-compose.yml."""
        with open(compose_path, 'r') as f:
            return yaml.safe_load(f)
    
    def merge_compose_files(self, base_compose: Dict, integration_compose: Dict) -> Dict:
        """
        Merge integration config into base compose.
        
        Used when user wants a single docker-compose.yml instead of separate files.
        """
        merged = base_compose.copy()
        
        # Add obs-stack network
        if 'networks' not in merged:
            merged['networks'] = {}
        merged['networks'][self.obs_stack_network] = integration_compose['networks'][self.obs_stack_network]
        
        # Merge service configurations
        for service_name, integration_config in integration_compose['services'].items():
            if service_name in merged['services']:
                # Add networks
                if 'networks' not in merged['services'][service_name]:
                    merged['services'][service_name]['networks'] = []
                merged['services'][service_name]['networks'].extend(integration_config['networks'])
                
                # Add environment
                if 'environment' not in merged['services'][service_name]:
                    merged['services'][service_name]['environment'] = []
                elif isinstance(merged['services'][service_name]['environment'], dict):
                    # Convert dict to list format
                    env_dict = merged['services'][service_name]['environment']
                    merged['services'][service_name]['environment'] = [
                        f"{k}={v}" for k, v in env_dict.items()
                    ]
                merged['services'][service_name]['environment'].extend(integration_config['environment'])
                
                # Add labels
                if 'labels' not in merged['services'][service_name]:
                    merged['services'][service_name]['labels'] = []
                elif isinstance(merged['services'][service_name]['labels'], dict):
                    # Convert dict to list format
                    labels_dict = merged['services'][service_name]['labels']
                    merged['services'][service_name]['labels'] = [
                        f"{k}={v}" for k, v in labels_dict.items()
                    ]
                merged['services'][service_name]['labels'].extend(integration_config['labels'])
        
        return merged
    
    def generate_full_stack_compose(self) -> str:
        """
        Generate a complete docker-compose.yml with both app and observability stack.
        
        Returns:
            YAML string of complete stack
        """
        compose = {
            'version': '3.8',
            'networks': {
                self.obs_stack_network: {
                    'name': self.obs_stack_network,
                    'driver': 'bridge'
                }
            },
            'volumes': {
                'prometheus_data': None,
                'grafana_data': None,
                'loki_data': None,
                'tempo_data': None,
            },
            'services': {
                # Include backend services
                'otel-collector': self._get_backend_service_config('otel-collector'),
                'prometheus': self._get_backend_service_config('prometheus'),
                'grafana': self._get_backend_service_config('grafana'),
                'loki': self._get_backend_service_config('loki'),
                'tempo': self._get_backend_service_config('tempo'),
            }
        }
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def _get_backend_service_config(self, service_name: str) -> Dict:
        """Get service config from backend compose."""
        # This would read from backend/docker-compose.yml
        # Simplified version for now
        configs = {
            'otel-collector': {
                'image': 'otel/opentelemetry-collector-contrib:0.91.0',
                'container_name': 'obs-stack-otel-collector',
                'command': ['--config=/etc/otel-collector-config.yml'],
                'volumes': ['./backend/otel-collector/config.yml:/etc/otel-collector-config.yml'],
                'ports': ['4317:4317', '4318:4318'],
                'networks': [self.obs_stack_network],
            },
            'prometheus': {
                'image': 'prom/prometheus:v2.48.0',
                'container_name': 'obs-stack-prometheus',
                'volumes': ['./backend/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml', 'prometheus_data:/prometheus'],
                'ports': ['9090:9090'],
                'networks': [self.obs_stack_network],
            },
            'grafana': {
                'image': 'grafana/grafana:10.2.2',
                'container_name': 'obs-stack-grafana',
                'environment': {
                    'GF_SECURITY_ADMIN_PASSWORD': 'obsstack',
                },
                'volumes': ['grafana_data:/var/lib/grafana', './backend/grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml'],
                'ports': ['3001:3000'],
                'networks': [self.obs_stack_network],
            },
            'loki': {
                'image': 'grafana/loki:2.9.3',
                'container_name': 'obs-stack-loki',
                'volumes': ['./backend/loki/config.yml:/etc/loki/config.yml', 'loki_data:/loki'],
                'ports': ['3100:3100'],
                'networks': [self.obs_stack_network],
            },
            'tempo': {
                'image': 'grafana/tempo:2.3.1',
                'container_name': 'obs-stack-tempo',
                'volumes': ['./backend/tempo/config.yml:/etc/tempo.yml', 'tempo_data:/tmp/tempo'],
                'ports': ['3200:3200'],
                'networks': [self.obs_stack_network],
            },
        }
        
        return configs.get(service_name, {})
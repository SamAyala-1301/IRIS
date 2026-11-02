"""Inject observability sidecars into running containers."""
import docker
from typing import List, Dict, Optional

class SidecarInjector:
    """Inject observability configuration into running containers."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.obs_stack_network = "obs-stack-network"
    
    def inject_into_container(self, container_id: str, framework: str) -> bool:
        """
        Inject observability into a running container.
        
        This connects the container to obs-stack network and adds required env vars.
        
        Args:
            container_id: Container ID or name
            framework: Detected framework (flask, django, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Connect to obs-stack network
            self._connect_to_network(container)
            
            # Add labels
            self._add_labels(container, framework)
            
            return True
            
        except Exception as e:
            print(f"Injection failed: {e}")
            return False
    
    def _connect_to_network(self, container):
        """Connect container to obs-stack network."""
        try:
            # Check if network exists
            network = self.docker_client.networks.get(self.obs_stack_network)
            
            # Check if already connected
            container.reload()
            networks = container.attrs['NetworkSettings']['Networks']
            
            if self.obs_stack_network not in networks:
                network.connect(container)
                print(f"✓ Connected {container.name} to {self.obs_stack_network}")
            else:
                print(f"✓ Already connected to {self.obs_stack_network}")
                
        except docker.errors.NotFound:
            print(f"⚠️  Network {self.obs_stack_network} not found. Run 'obs-stack up' first.")
            raise
    
    def _add_labels(self, container, framework: str):
        """Add obs-stack labels to container."""
        # Note: Labels can't be changed on running containers
        # This is for documentation - labels should be set at container creation
        print(f"ℹ️  Labels should be added at container creation time")
        print(f"   Add these to your docker-compose.yml:")
        print(f"   - obs_stack.enabled=true")
        print(f"   - obs_stack.framework={framework}")
    
    def inject_into_compose_service(
        self, 
        service_name: str, 
        compose_file: str = "docker-compose.yml"
    ) -> bool:
        """
        Inject observability into a docker-compose service.
        
        This modifies the compose file to add obs-stack integration.
        """
        try:
            import yaml
            
            # Read compose file
            with open(compose_file, 'r') as f:
                compose = yaml.safe_load(f)
            
            if service_name not in compose.get('services', {}):
                print(f"Service {service_name} not found in {compose_file}")
                return False
            
            service = compose['services'][service_name]
            
            # Add network
            if 'networks' not in service:
                service['networks'] = []
            if self.obs_stack_network not in service['networks']:
                service['networks'].append(self.obs_stack_network)
            
            # Add environment variables
            if 'environment' not in service:
                service['environment'] = []
            
            otel_vars = [
                'OTEL_EXPORTER_OTLP_ENDPOINT=http://obs-stack-otel-collector:4317',
                f'OTEL_SERVICE_NAME={service_name}',
            ]
            
            if isinstance(service['environment'], list):
                service['environment'].extend(otel_vars)
            else:
                # Dict format
                service['environment'].update({
                    'OTEL_EXPORTER_OTLP_ENDPOINT': 'http://obs-stack-otel-collector:4317',
                    'OTEL_SERVICE_NAME': service_name,
                })
            
            # Add labels
            if 'labels' not in service:
                service['labels'] = []
            
            labels = [
                'obs_stack.enabled=true',
                f'obs_stack.service={service_name}',
            ]
            
            if isinstance(service['labels'], list):
                service['labels'].extend(labels)
            else:
                # Dict format
                service['labels'].update({
                    'obs_stack.enabled': 'true',
                    'obs_stack.service': service_name,
                })
            
            # Add obs-stack network to compose
            if 'networks' not in compose:
                compose['networks'] = {}
            compose['networks'][self.obs_stack_network] = {
                'external': True,
                'name': self.obs_stack_network
            }
            
            # Write back
            with open(compose_file, 'w') as f:
                yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
            
            print(f"✓ Injected observability into {service_name}")
            return True
            
        except Exception as e:
            print(f"Injection failed: {e}")
            return False
    
    def batch_inject(self, container_ids: List[str]) -> Dict[str, bool]:
        """Inject into multiple containers."""
        results = {}
        
        for container_id in container_ids:
            try:
                # Detect framework first
                from ..detector.framework_detector import FrameworkDetector
                detector = FrameworkDetector()
                detection = detector.detect(container_id)
                
                # Inject
                success = self.inject_into_container(container_id, detection.framework.value)
                results[container_id] = success
                
            except Exception as e:
                print(f"Failed to inject {container_id}: {e}")
                results[container_id] = False
        
        return results
    
    def verify_injection(self, container_id: str) -> bool:
        """Verify that injection was successful."""
        try:
            container = self.docker_client.containers.get(container_id)
            container.reload()
            
            # Check network connection
            networks = container.attrs['NetworkSettings']['Networks']
            if self.obs_stack_network not in networks:
                return False
            
            return True
            
        except Exception:
            return False
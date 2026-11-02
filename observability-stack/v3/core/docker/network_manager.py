"""Manage Docker networks for ObsStack."""
import docker
from typing import List, Optional

class NetworkManager:
    """Manage Docker network for observability stack."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.obs_stack_network = "obs-stack-network"
    
    def create_network(self) -> bool:
        """Create obs-stack network if it doesn't exist."""
        try:
            # Check if network already exists
            try:
                network = self.docker_client.networks.get(self.obs_stack_network)
                print(f"✓ Network {self.obs_stack_network} already exists")
                return True
            except docker.errors.NotFound:
                pass
            
            # Create network
            network = self.docker_client.networks.create(
                self.obs_stack_network,
                driver="bridge",
                labels={
                    "obs_stack.managed": "true",
                    "obs_stack.version": "3.0.0"
                }
            )
            
            print(f"✓ Created network {self.obs_stack_network}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create network: {e}")
            return False
    
    def delete_network(self) -> bool:
        """Delete obs-stack network."""
        try:
            network = self.docker_client.networks.get(self.obs_stack_network)
            
            # Disconnect all containers first
            containers = network.attrs.get('Containers', {})
            for container_id in containers:
                try:
                    container = self.docker_client.containers.get(container_id)
                    network.disconnect(container)
                except:
                    pass
            
            # Remove network
            network.remove()
            print(f"✓ Deleted network {self.obs_stack_network}")
            return True
            
        except docker.errors.NotFound:
            print(f"ℹ️  Network {self.obs_stack_network} does not exist")
            return True
        except Exception as e:
            print(f"✗ Failed to delete network: {e}")
            return False
    
    def network_exists(self) -> bool:
        """Check if obs-stack network exists."""
        try:
            self.docker_client.networks.get(self.obs_stack_network)
            return True
        except docker.errors.NotFound:
            return False
    
    def list_connected_containers(self) -> List[str]:
        """List all containers connected to obs-stack network."""
        try:
            network = self.docker_client.networks.get(self.obs_stack_network)
            containers = network.attrs.get('Containers', {})
            
            container_names = []
            for container_id in containers:
                try:
                    container = self.docker_client.containers.get(container_id)
                    container_names.append(container.name)
                except:
                    pass
            
            return container_names
            
        except docker.errors.NotFound:
            return []
    
    def connect_container(self, container_id: str) -> bool:
        """Connect a container to obs-stack network."""
        try:
            # Ensure network exists
            if not self.network_exists():
                self.create_network()
            
            network = self.docker_client.networks.get(self.obs_stack_network)
            container = self.docker_client.containers.get(container_id)
            
            # Check if already connected
            container.reload()
            networks = container.attrs['NetworkSettings']['Networks']
            if self.obs_stack_network in networks:
                print(f"ℹ️  {container.name} already connected")
                return True
            
            # Connect
            network.connect(container)
            print(f"✓ Connected {container.name} to {self.obs_stack_network}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect container: {e}")
            return False
    
    def disconnect_container(self, container_id: str) -> bool:
        """Disconnect a container from obs-stack network."""
        try:
            network = self.docker_client.networks.get(self.obs_stack_network)
            container = self.docker_client.containers.get(container_id)
            
            network.disconnect(container)
            print(f"✓ Disconnected {container.name} from {self.obs_stack_network}")
            return True
            
        except docker.errors.NotFound:
            print(f"ℹ️  Container not connected to {self.obs_stack_network}")
            return True
        except Exception as e:
            print(f"✗ Failed to disconnect container: {e}")
            return False
    
    def get_network_info(self) -> Optional[dict]:
        """Get detailed network information."""
        try:
            network = self.docker_client.networks.get(self.obs_stack_network)
            return {
                'name': network.name,
                'id': network.id[:12],
                'driver': network.attrs.get('Driver'),
                'scope': network.attrs.get('Scope'),
                'containers': len(network.attrs.get('Containers', {})),
                'subnet': network.attrs.get('IPAM', {}).get('Config', [{}])[0].get('Subnet', 'N/A'),
            }
        except docker.errors.NotFound:
            return None
"""Integration tests for Docker functionality."""
import pytest
import docker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.docker.network_manager import NetworkManager
from core.docker.compose_generator import ComposeGenerator
from core.docker.sidecar_injector import SidecarInjector

@pytest.fixture(scope="module")
def docker_client():
    """Docker client fixture."""
    return docker.from_env()

@pytest.fixture(scope="module")
def network_manager():
    """Network manager fixture."""
    return NetworkManager()

@pytest.fixture(scope="module")
def compose_generator():
    """Compose generator fixture."""
    return ComposeGenerator()

@pytest.fixture(scope="module")
def sidecar_injector():
    """Sidecar injector fixture."""
    return SidecarInjector()

# Network Manager Tests
def test_create_network(network_manager):
    """Test network creation."""
    success = network_manager.create_network()
    assert success is True
    assert network_manager.network_exists() is True

def test_network_info(network_manager):
    """Test getting network info."""
    info = network_manager.get_network_info()
    assert info is not None
    assert info['name'] == 'obs-stack-network'
    assert 'id' in info
    assert 'driver' in info

def test_list_connected_containers(network_manager):
    """Test listing connected containers."""
    containers = network_manager.list_connected_containers()
    assert isinstance(containers, list)

def test_connect_disconnect_container(network_manager, docker_client):
    """Test connecting and disconnecting containers."""
    # Start a test container
    container = docker_client.containers.run(
        "alpine:latest",
        name="network-test",
        command="sleep 30",
        detach=True
    )
    
    try:
        # Connect
        success = network_manager.connect_container(container.id)
        assert success is True
        
        # Verify connection
        container.reload()
        networks = container.attrs['NetworkSettings']['Networks']
        assert 'obs-stack-network' in networks
        
        # Disconnect
        success = network_manager.disconnect_container(container.id)
        assert success is True
        
        # Verify disconnection
        container.reload()
        networks = container.attrs['NetworkSettings']['Networks']
        assert 'obs-stack-network' not in networks
        
    finally:
        container.stop()
        container.remove()

# Compose Generator Tests
def test_generate_integration_compose(compose_generator):
    """Test generating integration compose."""
    services = ['flask-app', 'express-app']
    compose = compose_generator.generate_integration_compose(services)
    
    assert 'version' in compose
    assert 'networks' in compose
    assert 'services' in compose
    assert 'obs-stack-network' in compose['networks']
    assert 'flask-app' in compose['services']
    assert 'express-app' in compose['services']

def test_service_integration_config(compose_generator):
    """Test service integration configuration."""
    config = compose_generator._generate_service_integration('test-service')
    
    assert 'networks' in config
    assert 'environment' in config
    assert 'labels' in config
    assert 'obs-stack-network' in config['networks']
    
    # Check environment variables
    env_list = config['environment']
    assert any('OTEL_EXPORTER_OTLP_ENDPOINT' in e for e in env_list)
    assert any('OTEL_SERVICE_NAME' in e for e in env_list)

def test_save_compose_file(compose_generator, tmp_path):
    """Test saving compose file."""
    services = ['test-app']
    compose = compose_generator.generate_integration_compose(services)
    
    output_file = tmp_path / "test-compose.yml"
    compose_generator.save_compose_file(compose, str(output_file))
    
    assert output_file.exists()
    
    # Verify content
    import yaml
    with open(output_file, 'r') as f:
        loaded = yaml.safe_load(f)
    
    assert loaded['services']['test-app'] is not None

# Sidecar Injector Tests
def test_inject_into_container(sidecar_injector, docker_client, network_manager):
    """Test injecting into a container."""
    # Ensure network exists
    network_manager.create_network()
    
    # Start test container
    container = docker_client.containers.run(
        "alpine:latest",
        name="inject-test",
        command="sleep 30",
        detach=True
    )
    
    try:
        # Inject
        success = sidecar_injector.inject_into_container(container.id, 'flask')
        assert success is True
        
        # Verify injection
        verified = sidecar_injector.verify_injection(container.id)
        assert verified is True
        
    finally:
        container.stop()
        container.remove()

def test_batch_inject(sidecar_injector, docker_client, network_manager):
    """Test batch injection."""
    # Ensure network exists
    network_manager.create_network()
    
    # Start multiple containers
    containers = []
    for i in range(3):
        container = docker_client.containers.run(
            "alpine:latest",
            name=f"batch-test-{i}",
            command="sleep 30",
            detach=True
        )
        containers.append(container)
    
    try:
        # Batch inject (will fail gracefully because not real apps)
        container_ids = [c.id for c in containers]
        results = sidecar_injector.batch_inject(container_ids)
        
        assert isinstance(results, dict)
        assert len(results) == 3
        
    finally:
        for container in containers:
            container.stop()
            container.remove()

# Cleanup
def test_cleanup_network(network_manager):
    """Test network cleanup (run last)."""
    # Don't actually delete in tests, just verify method exists
    assert hasattr(network_manager, 'delete_network')
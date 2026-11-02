"""Unit tests for instrumentation system."""
import pytest
import docker
import time
from core.instrumentor.orchestrator import InstrumentationOrchestrator
from core.instrumentor.base import InstrumentationStatus

@pytest.fixture(scope="module")
def docker_client():
    """Docker client fixture."""
    return docker.from_env()

@pytest.fixture(scope="module")
def orchestrator():
    """Orchestrator fixture."""
    return InstrumentationOrchestrator()

# Flask Instrumentation Tests
@pytest.fixture(scope="module")
def flask_container(docker_client):
    """Start Flask test container."""
    try:
        old = docker_client.containers.get("flask-instrument-test")
        old.stop()
        old.remove()
    except:
        pass
    
    container = docker_client.containers.run(
        "test-flask-app",
        name="flask-instrument-test",
        detach=True,
        ports={'5000/tcp': 5100}
    )
    time.sleep(3)
    yield container
    container.stop()
    container.remove()

def test_instrument_flask(orchestrator, flask_container):
    """Test Flask instrumentation."""
    result = orchestrator.instrument_container(flask_container.id)
    
    assert result.framework == "flask"
    assert result.status == InstrumentationStatus.INSTRUMENTED
    assert len(result.modifications) > 0
    assert "otel_init.py" in str(result.modifications)
    
    # Verify instrumentation
    verified = orchestrator.verify_instrumentation(flask_container.id)
    assert verified is True

def test_rollback_flask(orchestrator, flask_container):
    """Test Flask instrumentation rollback."""
    # First instrument
    orchestrator.instrument_container(flask_container.id)
    
    # Then rollback
    success = orchestrator.rollback_instrumentation(flask_container.id)
    assert success is True
    
    # Verify it's removed
    verified = orchestrator.verify_instrumentation(flask_container.id)
    assert verified is False

# Express Instrumentation Tests
@pytest.fixture(scope="module")
def express_container(docker_client):
    """Start Express test container."""
    try:
        old = docker_client.containers.get("express-instrument-test")
        old.stop()
        old.remove()
    except:
        pass
    
    container = docker_client.containers.run(
        "test-express-app",
        name="express-instrument-test",
        detach=True,
        ports={'3000/tcp': 3100}
    )
    time.sleep(3)
    yield container
    container.stop()
    container.remove()

def test_instrument_express(orchestrator, express_container):
    """Test Express instrumentation."""
    result = orchestrator.instrument_container(express_container.id)
    
    assert result.framework == "express"
    assert result.status == InstrumentationStatus.INSTRUMENTED
    assert len(result.modifications) > 0
    
    # Verify
    verified = orchestrator.verify_instrumentation(express_container.id)
    assert verified is True

def test_supported_frameworks(orchestrator):
    """Test getting supported frameworks."""
    frameworks = orchestrator.get_supported_frameworks()
    
    assert len(frameworks) >= 4  # Flask, Django, FastAPI, Express
    from core.detector.base import Framework
    assert Framework.FLASK in frameworks
    assert Framework.EXPRESS in frameworks

def test_instrument_unknown_container(orchestrator, docker_client):
    """Test instrumenting a container with unknown framework."""
    # Start a basic container without a framework
    container = docker_client.containers.run(
        "alpine:latest",
        name="unknown-test",
        command="sleep 30",
        detach=True
    )
    
    try:
        result = orchestrator.instrument_container(container.id)
        
        assert result.status == InstrumentationStatus.FAILED
        assert "unknown" in result.framework.lower() or "not detect" in result.error_message.lower()
    
    finally:
        container.stop()
        container.remove()
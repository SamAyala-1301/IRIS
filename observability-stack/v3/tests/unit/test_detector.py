import pytest
import docker
import time
from core.detector.framework_detector import FrameworkDetector
from core.detector.base import Framework, Language

@pytest.fixture(scope="module")
def docker_client():
    """Docker client fixture."""
    return docker.from_env()

@pytest.fixture(scope="module")
def detector():
    """Detector fixture."""
    return FrameworkDetector()

# Flask Tests
@pytest.fixture(scope="module")
def flask_container(docker_client):
    """Start Flask test container."""
    # Stop existing if running
    try:
        old = docker_client.containers.get("flask-test")
        old.stop()
        old.remove()
    except:
        pass
    
    container = docker_client.containers.run(
        "test-flask-app",
        name="flask-test",
        detach=True,
        ports={'5000/tcp': 5000},
        environment={'FLASK_APP': 'app.py', 'FLASK_ENV': 'production'}
    )
    time.sleep(3)  # Wait for startup
    yield container
    container.stop()
    container.remove()

def test_detect_flask(detector, flask_container):
    """Test Flask detection."""
    result = detector.detect(flask_container.id)
    
    assert result.framework == Framework.FLASK
    assert result.language == Language.PYTHON
    assert result.confidence > 0.5
    assert result.container_name == "flask-test"

# Django Tests
@pytest.fixture(scope="module")
def django_container(docker_client):
    """Start Django test container."""
    try:
        old = docker_client.containers.get("django-test")
        old.stop()
        old.remove()
    except:
        pass
    
    container = docker_client.containers.run(
        "test-django-app",
        name="django-test",
        detach=True,
        ports={'8000/tcp': 8001},
        environment={'DJANGO_SETTINGS_MODULE': 'myproject.settings'}
    )
    time.sleep(5)  # Django takes longer to start
    yield container
    container.stop()
    container.remove()

def test_detect_django(detector, django_container):
    """Test Django detection."""
    result = detector.detect(django_container.id)
    
    assert result.framework == Framework.DJANGO
    assert result.language == Language.PYTHON
    assert result.confidence > 0.5

# FastAPI Tests
@pytest.fixture(scope="module")
def fastapi_container(docker_client):
    """Start FastAPI test container."""
    try:
        old = docker_client.containers.get("fastapi-test")
        old.stop()
        old.remove()
    except:
        pass
    
    container = docker_client.containers.run(
        "test-fastapi-app",
        name="fastapi-test",
        detach=True,
        ports={'8000/tcp': 8002}
    )
    time.sleep(3)
    yield container
    container.stop()
    container.remove()

def test_detect_fastapi(detector, fastapi_container):
    """Test FastAPI detection."""
    result = detector.detect(fastapi_container.id)
    
    assert result.framework == Framework.FASTAPI
    assert result.language == Language.PYTHON
    assert result.confidence > 0.5

# Express Tests
@pytest.fixture(scope="module")
def express_container(docker_client):
    """Start Express test container."""
    try:
        old = docker_client.containers.get("express-test")
        old.stop()
        old.remove()
    except:
        pass
    
    container = docker_client.containers.run(
        "test-express-app",
        name="express-test",
        detach=True,
        ports={'3000/tcp': 3000},
        environment={'NODE_ENV': 'production'}
    )
    time.sleep(3)
    yield container
    container.stop()
    container.remove()

def test_detect_express(detector, express_container):
    """Test Express detection."""
    result = detector.detect(express_container.id)
    
    assert result.framework == Framework.EXPRESS
    assert result.language == Language.NODEJS
    assert result.confidence > 0.5


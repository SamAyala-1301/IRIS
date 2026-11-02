"""End-to-end integration tests."""
import pytest
import docker
import subprocess
import time

@pytest.fixture(scope="module")
def test_containers():
    """Start all test containers."""
    containers = []
    client = docker.from_env()
    
    # Start Flask
    try:
        flask = client.containers.run(
            "test-flask-app",
            name="e2e-flask",
            detach=True,
            ports={'5000/tcp': 5010},
            remove=True
        )
        containers.append(flask)
        time.sleep(2)
    except:
        pass
    
    # Start Express
    try:
        express = client.containers.run(
            "test-express-app",
            name="e2e-express",
            detach=True,
            ports={'3000/tcp': 3010},
            remove=True
        )
        containers.append(express)
        time.sleep(2)
    except:
        pass
    
    yield containers
    
    # Cleanup
    for container in containers:
        try:
            container.stop()
        except:
            pass

def test_detect_all_command(test_containers):
    """Test obs-stack detect-all command."""
    result = subprocess.run(
        ["obs-stack", "detect-all"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "e2e-flask" in result.stdout
    assert "e2e-express" in result.stdout

def test_validate_command():
    """Test obs-stack validate command."""
    result = subprocess.run(
        ["obs-stack", "validate", "e2e-flask"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "flask" in result.stdout.lower()

def test_list_frameworks_command():
    """Test obs-stack list-frameworks command."""
    result = subprocess.run(
        ["obs-stack", "list-frameworks"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "Flask" in result.stdout
    assert "Django" in result.stdout
    assert "Express" in result.stdout


# File: v3/pytest.ini
"""Pytest configuration."""
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests


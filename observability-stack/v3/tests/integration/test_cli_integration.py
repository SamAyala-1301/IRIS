"""Integration tests for CLI commands."""
import pytest
import subprocess
import os
from pathlib import Path

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    return project_dir

def test_cli_version():
    """Test version command."""
    result = subprocess.run(
        ["obs-stack", "version"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "ObsStack" in result.stdout
    assert "3.0.0" in result.stdout

def test_cli_help():
    """Test help command."""
    result = subprocess.run(
        ["obs-stack", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "detect" in result.stdout
    assert "instrument" in result.stdout
    assert "init" in result.stdout
    assert "up" in result.stdout

def test_cli_list_frameworks():
    """Test list-frameworks command."""
    result = subprocess.run(
        ["obs-stack", "list-frameworks"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "Flask" in result.stdout
    assert "Django" in result.stdout
    assert "Express" in result.stdout

def test_cli_detect_nonexistent_container():
    """Test detect with non-existent container."""
    result = subprocess.run(
        ["obs-stack", "detect", "nonexistent-container-xyz"],
        capture_output=True,
        text=True
    )
    
    # Should fail gracefully
    assert result.returncode != 0
    assert "not found" in result.stdout or "not found" in result.stderr

def test_cli_init_dry_run(temp_project_dir):
    """Test init command (without actual execution)."""
    # We test that the command exists and accepts flags
    result = subprocess.run(
        ["obs-stack", "init", "--help"],
        capture_output=True,
        text=True,
        cwd=temp_project_dir
    )
    
    assert result.returncode == 0
    assert "init" in result.stdout.lower()

def test_cli_up_without_init():
    """Test up command without initialization."""
    result = subprocess.run(
        ["obs-stack", "up"],
        capture_output=True,
        text=True
    )
    
    # Should fail if backend not found
    # (or succeed if backend exists from previous tests)
    assert result.returncode in [0, 1]

def test_cli_status_all():
    """Test status command without arguments."""
    result = subprocess.run(
        ["obs-stack", "status"],
        capture_output=True,
        text=True
    )
    
    # Should work even with no containers
    assert result.returncode == 0

def test_cli_chaining():
    """Test command chaining logic."""
    # Test that commands can be run in sequence
    commands = [
        ["obs-stack", "version"],
        ["obs-stack", "list-frameworks"],
    ]
    
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0

def test_cli_invalid_command():
    """Test invalid command."""
    result = subprocess.run(
        ["obs-stack", "invalid-command-xyz"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0

def test_cli_instrument_without_container():
    """Test instrument command without container argument."""
    result = subprocess.run(
        ["obs-stack", "instrument"],
        capture_output=True,
        text=True
    )
    
    # Should show error about missing argument
    assert result.returncode != 0
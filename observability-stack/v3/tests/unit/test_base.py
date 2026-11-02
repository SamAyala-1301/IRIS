"""Unit tests for base classes."""
import pytest
from core.detector.base import DetectionResult, Framework, Language

def test_detection_result_creation():
    """Test DetectionResult creation."""
    result = DetectionResult(
        container_id="abc123",
        container_name="test-container",
        framework=Framework.FLASK,
        language=Language.PYTHON,
        confidence=0.95
    )
    
    assert result.container_id == "abc123"
    assert result.framework == Framework.FLASK
    assert result.language == Language.PYTHON
    assert result.is_confident()

def test_low_confidence():
    """Test low confidence detection."""
    result = DetectionResult(
        container_id="abc123",
        container_name="test",
        framework=Framework.UNKNOWN,
        language=Language.UNKNOWN,
        confidence=0.3
    )
    
    assert not result.is_confident()

def test_confidence_threshold():
    """Test custom confidence threshold."""
    result = DetectionResult(
        container_id="abc123",
        container_name="test",
        framework=Framework.FLASK,
        language=Language.PYTHON,
        confidence=0.75
    )
    
    assert result.is_confident(0.7)
    assert not result.is_confident(0.8)


"""Framework detection engine."""
from .base import Detector, DetectionResult
from .framework_detector import FrameworkDetector

__all__ = ["Detector", "DetectionResult", "FrameworkDetector"]

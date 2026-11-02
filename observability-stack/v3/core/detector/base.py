"""Base classes for detection system."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class Framework(Enum):
    """Supported frameworks."""
    FLASK = "flask"
    DJANGO = "django"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    NESTJS = "nestjs"
    SPRING_BOOT = "spring_boot"
    UNKNOWN = "unknown"

class Language(Enum):
    """Supported languages."""
    PYTHON = "python"
    NODEJS = "nodejs"
    JAVA = "java"
    GO = "go"
    UNKNOWN = "unknown"

@dataclass
class DetectionResult:
    """Result of framework detection."""
    container_id: str
    container_name: str
    framework: Framework
    language: Language
    version: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if detection confidence exceeds threshold."""
        return self.confidence >= threshold

class Detector:
    """Base class for all detectors."""
    
    def detect(self, container_id: str) -> DetectionResult:
        """Detect framework in container."""
        raise NotImplementedError
    
    def get_indicators(self) -> Dict[str, any]:
        """Get detection indicators for this detector."""
        raise NotImplementedError

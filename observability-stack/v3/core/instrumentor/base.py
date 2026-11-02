"""Base classes for instrumentation system."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class InstrumentationStatus(Enum):
    """Status of instrumentation."""
    NOT_INSTRUMENTED = "not_instrumented"
    INSTRUMENTED = "instrumented"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class InstrumentationResult:
    """Result of instrumentation operation."""
    container_id: str
    container_name: str
    framework: str
    status: InstrumentationStatus
    metrics_endpoint: Optional[str] = None
    trace_endpoint: Optional[str] = None
    logs_endpoint: Optional[str] = None
    error_message: Optional[str] = None
    modifications: List[str] = None
    
    def __post_init__(self):
        if self.modifications is None:
            self.modifications = []
    
    def is_successful(self) -> bool:
        """Check if instrumentation succeeded."""
        return self.status == InstrumentationStatus.INSTRUMENTED
    
    def get_endpoints(self) -> Dict[str, str]:
        """Get all monitoring endpoints."""
        endpoints = {}
        if self.metrics_endpoint:
            endpoints['metrics'] = self.metrics_endpoint
        if self.trace_endpoint:
            endpoints['traces'] = self.trace_endpoint
        if self.logs_endpoint:
            endpoints['logs'] = self.logs_endpoint
        return endpoints

class Instrumentor:
    """Base class for framework instrumentors."""
    
    def instrument(self, container, detection_result) -> InstrumentationResult:
        """
        Instrument a container with OpenTelemetry.
        
        Args:
            container: Docker container object
            detection_result: DetectionResult from framework detection
        
        Returns:
            InstrumentationResult with status and endpoints
        """
        raise NotImplementedError
    
    def verify_instrumentation(self, container) -> bool:
        """Verify that instrumentation is working."""
        raise NotImplementedError
    
    def rollback(self, container) -> bool:
        """Rollback instrumentation changes."""
        raise NotImplementedError
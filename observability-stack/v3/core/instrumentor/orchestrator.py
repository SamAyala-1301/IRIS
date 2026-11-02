"""Main instrumentation orchestrator."""
import docker
from typing import Optional
from ..detector.framework_detector import FrameworkDetector
from ..detector.base import Framework
from .base import InstrumentationResult, InstrumentationStatus
from .python.flask_instrumentor import FlaskInstrumentor
from .python.django_instrumentor import DjangoInstrumentor
from .python.fastapi_instrumentor import FastAPIInstrumentor
from .nodejs.express_instrumentor import ExpressInstrumentor

class InstrumentationOrchestrator:
    """Orchestrate detection and instrumentation."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.detector = FrameworkDetector()
        
        # Framework-specific instrumentors
        self.instrumentors = {
            Framework.FLASK: FlaskInstrumentor(),
            Framework.DJANGO: DjangoInstrumentor(),
            Framework.FASTAPI: FastAPIInstrumentor(),
            Framework.EXPRESS: ExpressInstrumentor(),
        }
    
    def instrument_container(self, container_id: str) -> InstrumentationResult:
        """
        Detect and instrument a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            InstrumentationResult with status and details
        """
        try:
            # Get container
            container = self.docker_client.containers.get(container_id)
            
            # Detect framework
            print(f"🔍 Detecting framework in {container.name}...")
            detection_result = self.detector.detect(container_id)
            
            if detection_result.framework == Framework.UNKNOWN:
                return InstrumentationResult(
                    container_id=container_id,
                    container_name=container.name,
                    framework="unknown",
                    status=InstrumentationStatus.FAILED,
                    error_message="Could not detect framework"
                )
            
            print(f"✅ Detected: {detection_result.framework.value}")
            
            # Get appropriate instrumentor
            instrumentor = self.instrumentors.get(detection_result.framework)
            
            if not instrumentor:
                return InstrumentationResult(
                    container_id=container_id,
                    container_name=container.name,
                    framework=detection_result.framework.value,
                    status=InstrumentationStatus.FAILED,
                    error_message=f"Instrumentation not yet supported for {detection_result.framework.value}"
                )
            
            # Instrument
            print(f"🔧 Instrumenting {detection_result.framework.value}...")
            result = instrumentor.instrument(container, detection_result)
            
            return result
            
        except docker.errors.NotFound:
            return InstrumentationResult(
                container_id=container_id,
                container_name="unknown",
                framework="unknown",
                status=InstrumentationStatus.FAILED,
                error_message=f"Container {container_id} not found"
            )
        except Exception as e:
            return InstrumentationResult(
                container_id=container_id,
                container_name="unknown",
                framework="unknown",
                status=InstrumentationStatus.FAILED,
                error_message=str(e)
            )
    
    def verify_instrumentation(self, container_id: str) -> bool:
        """Verify that a container is instrumented."""
        try:
            container = self.docker_client.containers.get(container_id)
            detection_result = self.detector.detect(container_id)
            
            instrumentor = self.instrumentors.get(detection_result.framework)
            if not instrumentor:
                return False
            
            return instrumentor.verify_instrumentation(container)
            
        except Exception:
            return False
    
    def rollback_instrumentation(self, container_id: str) -> bool:
        """Rollback instrumentation for a container."""
        try:
            container = self.docker_client.containers.get(container_id)
            detection_result = self.detector.detect(container_id)
            
            instrumentor = self.instrumentors.get(detection_result.framework)
            if not instrumentor:
                return False
            
            return instrumentor.rollback(container)
            
        except Exception:
            return False
    
    def get_supported_frameworks(self) -> list:
        """Get list of supported frameworks for instrumentation."""
        return list(self.instrumentors.keys())
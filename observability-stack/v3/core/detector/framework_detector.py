"""Main framework detection orchestrator - OPTIMIZED WEIGHTS."""
import docker
from typing import Optional, Dict
from .base import Detector, DetectionResult, Framework, Language

from .scanners.port_scanner import PortScanner
from .scanners.process_scanner import ProcessScanner
from .scanners.http_prober import HTTPProber
from .analyzers.env_analyzer import EnvAnalyzer
from .analyzers.file_analyzer import FileAnalyzer
from .analyzers.package_analyzer import PackageAnalyzer


class FrameworkDetector(Detector):
    """Enhanced orchestrator with optimized weights."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        
        self.port_scanner = PortScanner()
        self.process_scanner = ProcessScanner()
        self.http_prober = HTTPProber()
        self.env_analyzer = EnvAnalyzer()
        self.file_analyzer = FileAnalyzer()
        self.package_analyzer = PackageAnalyzer()
    
    def detect(self, container_id: str) -> DetectionResult:
        """Detect framework using ALL available strategies."""
        try:
            container = self.docker_client.containers.get(container_id)
            container_name = container.name
            
            print(f"🔍 Scanning container: {container_name}")
            
            # Run ALL detection strategies
            print("  ├─ Port scanning...")
            port_hints = self.port_scanner.scan(container)
            
            print("  ├─ Process analysis...")
            process_hints = self.process_scanner.scan(container)
            
            print("  ├─ HTTP probing...")
            http_hints = self.http_prober.probe(container)
            
            print("  ├─ Environment variables...")
            env_hints = self.env_analyzer.analyze(container)
            
            print("  ├─ File system...")
            file_hints = self.file_analyzer.analyze(container)
            
            print("  └─ Package analysis...")
            package_hints = self.package_analyzer.analyze(container)
            
            # Combine results
            framework, language, confidence, version = self._combine_results(
                port_hints, 
                process_hints,
                http_hints,
                env_hints, 
                file_hints,
                package_hints
            )
            
            return DetectionResult(
                container_id=container_id,
                container_name=container_name,
                framework=framework,
                language=language,
                version=version,
                confidence=confidence,
                metadata={
                    "port_hints": port_hints,
                    "process_hints": process_hints,
                    "http_hints": http_hints,
                    "env_hints": env_hints,
                    "file_hints": file_hints,
                    "package_hints": package_hints
                }
            )
            
        except docker.errors.NotFound:
            raise ValueError(f"Container {container_id} not found")
        except Exception as e:
            raise RuntimeError(f"Detection failed: {e}")
    
    def _combine_results(self, port_hints, process_hints, http_hints, 
                        env_hints, file_hints, package_hints):
        """
        Combine with OPTIMIZED weights.
        
        NEW Weights (realistic for production):
        - Package: 0.45 (most reliable)
        - File: 0.35 (very reliable)
        - Process: 0.30 (reliable when available)
        - Environment: 0.25 (good signal)
        - HTTP: 0.20 (can be spoofed)
        - Port: 0.10 (weakest signal)
        """
        scores = {}
        version_hints = {}
        
        # OPTIMIZED WEIGHTS
        weights = {
            "package": 0.45,
            "file": 0.35,
            "process": 0.30,
            "env": 0.25,
            "http": 0.20,
            "port": 0.10
        }
        
        # Aggregate scores
        for hint_type, hints, weight in [
            ("package", package_hints, weights["package"]),
            ("file", file_hints, weights["file"]),
            ("process", process_hints, weights["process"]),
            ("env", env_hints, weights["env"]),
            ("http", http_hints, weights["http"]),
            ("port", port_hints, weights["port"])
        ]:
            for key, score in hints.items():
                # Check if version hint
                if isinstance(key, str) and '_version' in key:
                    framework_name = key.replace('_version', '')
                    version_hints[framework_name] = score
                elif isinstance(key, Framework):
                    if key not in scores:
                        scores[key] = 0
                    scores[key] += score * weight
        
        if not scores:
            return Framework.UNKNOWN, Language.UNKNOWN, 0.0, None
        
        # Get best framework
        best_framework = max(scores, key=scores.get)
        confidence = min(scores[best_framework], 1.0)
        
        # Get version
        version = version_hints.get(best_framework.value, None)
        
        # Map to language
        language_map = {
            Framework.FLASK: Language.PYTHON,
            Framework.DJANGO: Language.PYTHON,
            Framework.FASTAPI: Language.PYTHON,
            Framework.EXPRESS: Language.NODEJS,
            Framework.NESTJS: Language.NODEJS,
            Framework.SPRING_BOOT: Language.JAVA,
        }
        
        language = language_map.get(best_framework, Language.UNKNOWN)
        
        return best_framework, language, confidence, version
    
    def get_indicators(self) -> dict:
        """Get all detection indicators."""
        return {
            "port_indicators": self.port_scanner.get_indicators(),
            "process_indicators": self.process_scanner.get_indicators(),
            "http_indicators": self.http_prober.get_indicators(),
            "env_indicators": self.env_analyzer.get_indicators(),
            "file_indicators": self.file_analyzer.get_indicators(),
            "package_indicators": self.package_analyzer.get_indicators()
        }
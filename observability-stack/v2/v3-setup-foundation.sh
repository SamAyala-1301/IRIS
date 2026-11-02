#!/bin/bash
# V3 Foundation Setup Script - Day 0
# Run this to set up complete V3 structure in 5 minutes

set -e  # Exit on error

echo "🚀 ObsStack V3 - Foundation Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Run this from your observability-stack root directory"
    exit 1
fi

echo -e "${BLUE}Step 1: Backing up V2${NC}"
# Create backup branch
git checkout -b v2-stable 2>/dev/null || git checkout v2-stable
git tag v2.0.0 2>/dev/null || echo "Tag v2.0.0 already exists"

# Go back to main
git checkout main 2>/dev/null || git checkout master

echo -e "${GREEN}✓${NC} V2 backed up to branch 'v2-stable' and tagged v2.0.0"
echo ""

echo -e "${BLUE}Step 2: Restructuring to Monorepo${NC}"
# Create v2 directory if it doesn't exist
if [ ! -d "v2" ]; then
    mkdir v2
    echo "Moving existing files to v2/..."
    
    # Move all files except .git and v2 itself
    for item in * .[^.]*; do
        if [ "$item" != ".git" ] && [ "$item" != "v2" ] && [ "$item" != "." ] && [ "$item" != ".." ]; then
            mv "$item" v2/ 2>/dev/null || true
        fi
    done
fi

echo -e "${GREEN}✓${NC} V2 files moved to v2/ directory"
echo ""

echo -e "${BLUE}Step 3: Creating V3 Directory Structure${NC}"
# Create V3 structure
mkdir -p v3/{core,docker-plugin,k8s-operator,backend,cli,tests,docs,scripts}

# Core modules
mkdir -p v3/core/{detector,instrumentor,config_generator,common}
mkdir -p v3/core/detector/{scanners,analyzers,fingerprinters}
mkdir -p v3/core/instrumentor/{python,nodejs,java,generic}
mkdir -p v3/core/config_generator/{dashboards,alerts,rules}

# Backend (monitoring stack)
mkdir -p v3/backend/{prometheus,grafana,tempo,loki,alertmanager,otel}
mkdir -p v3/backend/grafana/{dashboards,datasources,templates}
mkdir -p v3/backend/prometheus/{rules,configs,templates}

# CLI structure
mkdir -p v3/cli/{commands,utils}

# Tests
mkdir -p v3/tests/{unit,integration,e2e,test-apps}
mkdir -p v3/tests/test-apps/{flask-app,express-app,django-app}

# Documentation
mkdir -p v3/docs/{architecture,tutorials,api-reference,screenshots}

echo -e "${GREEN}✓${NC} V3 directory structure created"
echo ""

echo -e "${BLUE}Step 4: Creating Core Python Files${NC}"

# Main __init__.py
cat > v3/__init__.py << 'PYEOF'
"""
ObsStack V3 - Instant Observability for Any App
Auto-detection and instrumentation system
"""
__version__ = "3.0.0-alpha"
__author__ = "Naga Sowmya Ganti"
PYEOF

# Core detector base
cat > v3/core/detector/__init__.py << 'PYEOF'
"""Framework detection engine."""
from .base import Detector, DetectionResult
from .framework_detector import FrameworkDetector

__all__ = ["Detector", "DetectionResult", "FrameworkDetector"]
PYEOF

cat > v3/core/detector/base.py << 'PYEOF'
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
PYEOF

# Framework detector implementation
cat > v3/core/detector/framework_detector.py << 'PYEOF'
"""Main framework detection orchestrator."""
import docker
from typing import Optional
from .base import Detector, DetectionResult, Framework, Language
from .scanners.port_scanner import PortScanner
from .analyzers.env_analyzer import EnvAnalyzer
from .analyzers.file_analyzer import FileAnalyzer

class FrameworkDetector(Detector):
    """Orchestrates multiple detection strategies."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.port_scanner = PortScanner()
        self.env_analyzer = EnvAnalyzer()
        self.file_analyzer = FileAnalyzer()
    
    def detect(self, container_id: str) -> DetectionResult:
        """
        Detect framework using multiple strategies.
        Combines results from port scanning, env vars, and file analysis.
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Get container info
            container_name = container.name
            
            # Run all detection strategies
            port_result = self.port_scanner.scan(container)
            env_result = self.env_analyzer.analyze(container)
            file_result = self.file_analyzer.analyze(container)
            
            # Combine results (weighted average)
            framework, language, confidence = self._combine_results(
                port_result, env_result, file_result
            )
            
            return DetectionResult(
                container_id=container_id,
                container_name=container_name,
                framework=framework,
                language=language,
                confidence=confidence,
                metadata={
                    "port_hints": port_result,
                    "env_hints": env_result,
                    "file_hints": file_result
                }
            )
            
        except docker.errors.NotFound:
            raise ValueError(f"Container {container_id} not found")
        except Exception as e:
            raise RuntimeError(f"Detection failed: {e}")
    
    def _combine_results(self, port_hints, env_hints, file_hints):
        """Combine detection results with weighted scoring."""
        # Simple implementation - can be made more sophisticated
        scores = {}
        
        # Weight: files > env > ports
        weights = {"file": 0.5, "env": 0.3, "port": 0.2}
        
        # Aggregate scores
        for hint_type, hints, weight in [
            ("file", file_hints, weights["file"]),
            ("env", env_hints, weights["env"]),
            ("port", port_hints, weights["port"])
        ]:
            for framework, score in hints.items():
                if framework not in scores:
                    scores[framework] = 0
                scores[framework] += score * weight
        
        if not scores:
            return Framework.UNKNOWN, Language.UNKNOWN, 0.0
        
        # Get highest scoring framework
        best_framework = max(scores, key=scores.get)
        confidence = scores[best_framework]
        
        # Map framework to language
        language_map = {
            Framework.FLASK: Language.PYTHON,
            Framework.DJANGO: Language.PYTHON,
            Framework.FASTAPI: Language.PYTHON,
            Framework.EXPRESS: Language.NODEJS,
            Framework.NESTJS: Language.NODEJS,
            Framework.SPRING_BOOT: Language.JAVA,
        }
        
        language = language_map.get(best_framework, Language.UNKNOWN)
        
        return best_framework, language, confidence
    
    def get_indicators(self) -> dict:
        """Get all detection indicators."""
        return {
            "port_indicators": self.port_scanner.get_indicators(),
            "env_indicators": self.env_analyzer.get_indicators(),
            "file_indicators": self.file_analyzer.get_indicators()
        }
PYEOF

# Port scanner
cat > v3/core/detector/scanners/__init__.py << 'PYEOF'
"""Scanner modules for container inspection."""
PYEOF

cat > v3/core/detector/scanners/port_scanner.py << 'PYEOF'
"""Port scanning for framework hints."""
from ..base import Framework

class PortScanner:
    """Scan container ports for framework hints."""
    
    PORT_HINTS = {
        5000: Framework.FLASK,
        8000: Framework.DJANGO,
        8080: Framework.SPRING_BOOT,
        3000: Framework.EXPRESS,
        4000: Framework.EXPRESS,
    }
    
    def scan(self, container) -> dict:
        """Scan container ports and return framework hints."""
        hints = {}
        
        try:
            # Get port bindings
            ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            
            for port_key in ports.keys():
                # Extract port number (e.g., "5000/tcp" -> 5000)
                port = int(port_key.split('/')[0])
                
                # Check if port matches known framework
                if port in self.PORT_HINTS:
                    framework = self.PORT_HINTS[port]
                    hints[framework] = hints.get(framework, 0) + 0.3
        
        except Exception as e:
            print(f"Port scan error: {e}")
        
        return hints
    
    def get_indicators(self) -> dict:
        """Get port indicators."""
        return {"port_mappings": self.PORT_HINTS}
PYEOF

# Environment analyzer
cat > v3/core/detector/analyzers/__init__.py << 'PYEOF'
"""Analyzer modules for container inspection."""
PYEOF

cat > v3/core/detector/analyzers/env_analyzer.py << 'PYEOF'
"""Environment variable analysis."""
from ..base import Framework

class EnvAnalyzer:
    """Analyze environment variables for framework hints."""
    
    ENV_HINTS = {
        "FLASK_APP": Framework.FLASK,
        "DJANGO_SETTINGS_MODULE": Framework.DJANGO,
        "FASTAPI_ENV": Framework.FASTAPI,
        "NODE_ENV": Framework.EXPRESS,
        "SPRING_PROFILES_ACTIVE": Framework.SPRING_BOOT,
    }
    
    def analyze(self, container) -> dict:
        """Analyze environment variables."""
        hints = {}
        
        try:
            env_vars = container.attrs.get('Config', {}).get('Env', [])
            
            for env_var in env_vars:
                key = env_var.split('=')[0]
                
                if key in self.ENV_HINTS:
                    framework = self.ENV_HINTS[key]
                    hints[framework] = hints.get(framework, 0) + 0.4
        
        except Exception as e:
            print(f"Env analysis error: {e}")
        
        return hints
    
    def get_indicators(self) -> dict:
        """Get environment indicators."""
        return {"env_mappings": self.ENV_HINTS}
PYEOF

# File analyzer
cat > v3/core/detector/analyzers/file_analyzer.py << 'PYEOF'
"""File system analysis for framework detection."""
from ..base import Framework

class FileAnalyzer:
    """Analyze container filesystem for framework hints."""
    
    FILE_HINTS = {
        "requirements.txt": {Framework.FLASK: ["flask"], Framework.DJANGO: ["django"], Framework.FASTAPI: ["fastapi"]},
        "package.json": {Framework.EXPRESS: ["express"], Framework.NESTJS: ["@nestjs/core"]},
        "pom.xml": {Framework.SPRING_BOOT: ["spring-boot"]},
    }
    
    def analyze(self, container) -> dict:
        """Analyze files in container."""
        hints = {}
        
        try:
            # Try to exec into container and check for files
            for filename, framework_patterns in self.FILE_HINTS.items():
                try:
                    # Check if file exists
                    exec_result = container.exec_run(f"test -f {filename}")
                    
                    if exec_result.exit_code == 0:
                        # File exists, try to read it
                        content_result = container.exec_run(f"cat {filename}")
                        content = content_result.output.decode('utf-8', errors='ignore')
                        
                        # Check for framework patterns
                        for framework, patterns in framework_patterns.items():
                            for pattern in patterns:
                                if pattern.lower() in content.lower():
                                    hints[framework] = hints.get(framework, 0) + 0.6
                
                except Exception:
                    continue
        
        except Exception as e:
            print(f"File analysis error: {e}")
        
        return hints
    
    def get_indicators(self) -> dict:
        """Get file indicators."""
        return {"file_patterns": self.FILE_HINTS}
PYEOF

echo -e "${GREEN}✓${NC} Core detection modules created"
echo ""

echo -e "${BLUE}Step 5: Creating CLI${NC}"

cat > v3/cli/__init__.py << 'PYEOF'
"""Command-line interface for ObsStack."""
PYEOF

cat > v3/cli/main.py << 'PYEOF'
#!/usr/bin/env python3
"""Main CLI entry point."""
import click
from rich.console import Console
from rich.table import Table
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detector.framework_detector import FrameworkDetector

console = Console()

@click.group()
def cli():
    """🚀 ObsStack V3 - Instant Observability for Any App"""
    pass

@cli.command()
def version():
    """Show version information."""
    console.print("[bold blue]ObsStack v3.0.0-alpha[/bold blue]")
    console.print("Auto-detection and instrumentation system")

@cli.command()
@click.argument('container')
def detect(container):
    """
    Detect framework running in a container.
    
    CONTAINER: Container ID or name
    """
    console.print(f"\n🔍 Detecting framework in container: [cyan]{container}[/cyan]\n")
    
    try:
        detector = FrameworkDetector()
        result = detector.detect(container)
        
        # Create results table
        table = Table(title="Detection Results", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Container ID", result.container_id[:12])
        table.add_row("Container Name", result.container_name)
        table.add_row("Framework", result.framework.value)
        table.add_row("Language", result.language.value)
        table.add_row("Confidence", f"{result.confidence:.2%}")
        
        console.print(table)
        
        # Show metadata
        if result.metadata:
            console.print("\n[bold]Detection Details:[/bold]")
            for key, value in result.metadata.items():
                console.print(f"  {key}: {value}")
        
        # Confidence check
        if result.is_confident():
            console.print(f"\n[bold green]✓[/bold green] High confidence detection")
        else:
            console.print(f"\n[bold yellow]⚠[/bold yellow] Low confidence - may need manual verification")
        
    except ValueError as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Unexpected error:[/bold red] {e}")
        sys.exit(1)

@cli.command()
def list_indicators():
    """Show all detection indicators."""
    detector = FrameworkDetector()
    indicators = detector.get_indicators()
    
    console.print("\n[bold]Detection Indicators:[/bold]\n")
    
    for category, data in indicators.items():
        console.print(f"[cyan]{category}:[/cyan]")
        console.print(f"  {data}\n")

if __name__ == '__main__':
    cli()
PYEOF

chmod +x v3/cli/main.py

echo -e "${GREEN}✓${NC} CLI created"
echo ""

echo -e "${BLUE}Step 6: Creating requirements.txt${NC}"

cat > v3/requirements.txt << 'REQEOF'
# Core Dependencies
docker==7.0.0
pyyaml==6.0.1
jinja2==3.1.2
click==8.1.7
rich==13.7.0
requests==2.31.0

# OpenTelemetry
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-otlp==1.21.0

# Testing
pytest==7.4.3
pytest-docker==2.0.1

# Development
black==23.12.1
flake8==6.1.0
REQEOF

echo -e "${GREEN}✓${NC} requirements.txt created"
echo ""

echo -e "${BLUE}Step 7: Creating setup.py${NC}"

cat > v3/setup.py << 'SETUPEOF'
from setuptools import setup, find_packages

setup(
    name="obs-stack",
    version="3.0.0-alpha",
    description="Instant Observability for Any App",
    author="Naga Sowmya Ganti",
    packages=find_packages(),
    install_requires=[
        "docker>=7.0.0",
        "pyyaml>=6.0.1",
        "jinja2>=3.1.2",
        "click>=8.1.7",
        "rich>=13.7.0",
        "requests>=2.31.0",
    ],
    entry_points={
        'console_scripts': [
            'obs-stack=cli.main:cli',
        ],
    },
    python_requires='>=3.10',
)
SETUPEOF

echo -e "${GREEN}✓${NC} setup.py created"
echo ""

echo -e "${BLUE}Step 8: Creating test files${NC}"

# Test for detector
cat > v3/tests/unit/test_detector.py << 'TESTEOF'
"""Unit tests for detector module."""
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
TESTEOF

# Test Flask app
mkdir -p v3/tests/test-apps/flask-app
cat > v3/tests/test-apps/flask-app/app.py << 'FLASKEOF'
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({"message": "Hello from Flask!"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
FLASKEOF

cat > v3/tests/test-apps/flask-app/requirements.txt << 'FLASKREQEOF'
flask==3.0.0
FLASKREQEOF

cat > v3/tests/test-apps/flask-app/Dockerfile << 'FLASKDOCKEREOF'
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
FLASKDOCKEREOF

echo -e "${GREEN}✓${NC} Test files created"
echo ""

echo -e "${BLUE}Step 9: Creating README files${NC}"

cat > v3/README.md << 'READMEEOF'
# ObsStack V3 - Instant Observability for Any App

**Status:** 🚧 Alpha - Active Development

## What is ObsStack V3?

A plug-and-play observability solution that automatically detects your application framework and instruments it with monitoring - **zero code changes required**.

```bash
# That's it! Observability added.
curl -sSL https://get.obs-stack.io | bash
docker compose up -d
```

## Features

- 🔍 **Auto-Detection:** Identifies Flask, Django, Express, Spring Boot, and more
- 🎯 **Auto-Instrumentation:** Injects metrics, logs, and traces automatically
- 📊 **Auto-Dashboards:** Generates framework-specific Grafana dashboards
- 🚨 **Smart Alerts:** Pre-configured alerting with sensible defaults
- 🔒 **PII Redaction:** Automatically redacts sensitive data
- ⚡ **<5% Overhead:** Minimal performance impact

## Quick Start

```bash
# Install
obs-stack init

# Detect your app
obs-stack detect my-app-container

# Start monitoring
docker compose -f docker-compose.yml -f obs-stack.yml up -d
```

## Project Status

- [x] Sprint 0: Foundation (Week 1) - **IN PROGRESS**
- [ ] Sprint 1: Auto-Detection (Weeks 2-3)
- [ ] Sprint 2: Auto-Instrumentation (Weeks 4-5)
- [ ] Sprint 3: Configuration Engine (Week 6)
- [ ] Sprint 4: Docker Plugin (Week 7)
- [ ] Sprint 5: Testing & Docs (Week 8)
- [ ] Sprint 6: Kubernetes Support (Weeks 9-10)
- [ ] Sprint 7: Advanced Features (Week 11)
- [ ] Sprint 8: Release (Week 12)

## Development

```bash
# Setup
cd v3
python3.10 -m venv venv
source venv/bin/activate
pip install -e .

# Run CLI
obs-stack version
obs-stack detect <container-name>

# Run tests
pytest tests/
```

## Architecture

```
ObsStack V3
├── core/               # Detection & instrumentation engine
├── docker-plugin/      # Docker Compose integration
├── k8s-operator/       # Kubernetes operator
├── backend/            # Monitoring stack (Prometheus, Grafana, etc.)
└── cli/               # Command-line interface
```

## Contributing

We're in active development! Check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE)
READMEEOF

cat > README.md << 'MAINREADMEEOF'
# Observability Stack - V2 & V3

**Two versions, two purposes:**

## 🎓 V2: Learn Production Observability

A complete, production-ready distributed observability platform for learning. Includes 4 microservices, Redis caching, RabbitMQ, and full monitoring stack.

**Purpose:** Educational - understand how observability works
**Audience:** Students, engineers building knowledge
**Status:** ✅ Stable - No new features

→ [Explore V2](v2/README.md)

---

## 🚀 V3: Instant Observability (Alpha)

Plug-and-play observability for ANY application. Auto-detects your framework and adds monitoring with zero code changes.

**Purpose:** Production tool - add observability instantly
**Audience:** Developers, DevOps engineers
**Status:** 🚧 Alpha - Active development

→ [Try V3](v3/README.md)

---

## Choose Your Path

- **Learning how observability works?** → Start with V2
- **Need to monitor your app?** → Use V3
- **Want to contribute?** → V3 needs help!

## Quick Comparison

| Feature | V2 | V3 |
|---------|----|----|
| **Purpose** | Learn & understand | Plug & play |
| **Setup Time** | 30 minutes | <5 minutes |
| **Code Changes** | Build from scratch | Zero changes |
| **Audience** | Students | Developers |
| **Status** | Stable | Alpha |

## Repository Structure

```
observability-stack/
├── v2/                 # Production learning stack (stable)
│   ├── services/       # Demo microservices
│   ├── dashboards/     # Pre-built dashboards
│   └── README.md       # V2 documentation
│
├── v3/                 # Plug-and-play platform (alpha)
│   ├── core/           # Auto-detection engine
│   ├── cli/            # Command-line tool
│   └── README.md       # V3 documentation
│
└── README.md          # This file
```

## Star History

If you find this useful, please star the repo! ⭐

## Author

**Naga Sowmya Ganti**
- GitHub: [@SamAyala-1301](https://github.com/SamAyala-1301)

## License

MIT License - see [LICENSE](LICENSE)
MAINREADMEEOF

echo -e "${GREEN}✓${NC} README files created"
echo ""

echo -e "${BLUE}Step 10: Creating .gitignore${NC}"

cat > v3/.gitignore << 'GITEOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
dist/
build/
*.egg-info/
GITEOF

echo -e "${GREEN}✓${NC} .gitignore created"
echo ""

echo "✅ Foundation setup complete!"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. cd v3"
echo "2. python3.10 -m venv venv"
echo "3. source venv/bin/activate"
echo "4. pip install -e ."
echo "5. obs-stack version"
echo ""
echo -e "${GREEN}Ready to start Sprint 1! 🚀${NC}"
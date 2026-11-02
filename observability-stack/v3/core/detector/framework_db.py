"""Comprehensive framework signature database."""
from dataclasses import dataclass, field
from typing import Dict, List, Set
from .base import Framework, Language

@dataclass
class FrameworkSignature:
    """Complete signature for a framework."""
    framework: Framework
    language: Language
    display_name: str
    description: str
    
    # Detection indicators
    file_patterns: List[str] = field(default_factory=list)
    package_names: List[str] = field(default_factory=list)
    env_var_keys: List[str] = field(default_factory=list)
    process_patterns: List[str] = field(default_factory=list)
    http_headers: Dict[str, str] = field(default_factory=dict)
    common_ports: List[int] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    
    # Version detection
    version_files: Dict[str, str] = field(default_factory=dict)
    
    # Confidence weights for each indicator type
    weights: Dict[str, float] = field(default_factory=dict)


# Complete Framework Database
FRAMEWORK_DATABASE = {
    Framework.FLASK: FrameworkSignature(
        framework=Framework.FLASK,
        language=Language.PYTHON,
        display_name="Flask",
        description="Lightweight Python WSGI web application framework",
        
        file_patterns=[
            "app.py",
            "application.py",
            "wsgi.py",
            "requirements.txt",
            "Pipfile",
        ],
        package_names=[
            "flask",
            "Flask",
            "flask-cors",
            "flask-sqlalchemy",
        ],
        env_var_keys=[
            "FLASK_APP",
            "FLASK_ENV",
            "FLASK_DEBUG",
        ],
        process_patterns=[
            r"python.*flask",
            r"flask\s+run",
            r"gunicorn.*:app",
        ],
        http_headers={
            "Server": "Werkzeug",
            "X-Powered-By": "Flask",
        },
        common_ports=[5000, 8000],
        endpoints=["/health", "/ping"],
        
        version_files={
            "requirements.txt": r"[Ff]lask[=><]+(\d+\.\d+\.?\d*)",
            "Pipfile": r"[Ff]lask.*['\"](\d+\.\d+\.?\d*)",
        },
        
        weights={
            "package": 0.9,
            "process": 0.8,
            "env": 0.7,
            "file": 0.6,
            "http": 0.5,
            "port": 0.3,
        }
    ),
    
    Framework.DJANGO: FrameworkSignature(
        framework=Framework.DJANGO,
        language=Language.PYTHON,
        display_name="Django",
        description="High-level Python web framework",
        
        file_patterns=[
            "manage.py",
            "settings.py",
            "wsgi.py",
            "asgi.py",
            "urls.py",
        ],
        package_names=[
            "django",
            "Django",
            "djangorestframework",
        ],
        env_var_keys=[
            "DJANGO_SETTINGS_MODULE",
            "DJANGO_SECRET_KEY",
            "DJANGO_DEBUG",
        ],
        process_patterns=[
            r"python.*manage\.py",
            r"django-admin",
            r"gunicorn.*django",
        ],
        http_headers={
            "X-Frame-Options": "DENY",  # Django default
        },
        common_ports=[8000, 8080],
        endpoints=["/admin/", "/api/"],
        
        version_files={
            "requirements.txt": r"[Dd]jango[=><]+(\d+\.\d+\.?\d*)",
        },
        
        weights={
            "package": 0.9,
            "file": 0.85,
            "process": 0.8,
            "env": 0.75,
            "endpoint": 0.7,
        }
    ),
    
    Framework.FASTAPI: FrameworkSignature(
        framework=Framework.FASTAPI,
        language=Language.PYTHON,
        display_name="FastAPI",
        description="Modern, fast Python web framework",
        
        file_patterns=[
            "main.py",
            "app.py",
            "requirements.txt",
        ],
        package_names=[
            "fastapi",
            "FastAPI",
            "uvicorn",
            "starlette",
        ],
        env_var_keys=[
            "FASTAPI_ENV",
        ],
        process_patterns=[
            r"uvicorn.*:app",
            r"python.*fastapi",
        ],
        http_headers={
            "Server": "uvicorn",
        },
        common_ports=[8000, 80],
        endpoints=["/docs", "/redoc", "/openapi.json"],
        
        version_files={
            "requirements.txt": r"[Ff]astapi[=><]+(\d+\.\d+\.?\d*)",
        },
        
        weights={
            "package": 0.95,
            "process": 0.9,
            "endpoint": 0.85,
            "http": 0.7,
        }
    ),
    
    Framework.EXPRESS: FrameworkSignature(
        framework=Framework.EXPRESS,
        language=Language.NODEJS,
        display_name="Express.js",
        description="Fast, unopinionated Node.js web framework",
        
        file_patterns=[
            "package.json",
            "app.js",
            "server.js",
            "index.js",
        ],
        package_names=[
            "express",
            "body-parser",
            "morgan",
        ],
        env_var_keys=[
            "NODE_ENV",
            "PORT",
        ],
        process_patterns=[
            r"node.*express",
            r"node.*app\.js",
            r"node.*server\.js",
            r"npm.*start",
        ],
        http_headers={
            "X-Powered-By": "Express",
        },
        common_ports=[3000, 8080, 80],
        endpoints=["/api", "/health"],
        
        version_files={
            "package.json": r'"express":\s*"[^"]*(\d+\.\d+\.?\d*)',
        },
        
        weights={
            "package": 0.95,
            "process": 0.85,
            "http": 0.8,
            "file": 0.7,
        }
    ),
    
    Framework.NESTJS: FrameworkSignature(
        framework=Framework.NESTJS,
        language=Language.NODEJS,
        display_name="NestJS",
        description="Progressive Node.js framework",
        
        file_patterns=[
            "package.json",
            "main.ts",
            "app.module.ts",
            "nest-cli.json",
        ],
        package_names=[
            "@nestjs/core",
            "@nestjs/common",
            "@nestjs/platform-express",
        ],
        env_var_keys=[
            "NODE_ENV",
        ],
        process_patterns=[
            r"node.*nest",
            r"nest\s+start",
        ],
        http_headers={
            "X-Powered-By": "Express",  # NestJS uses Express under the hood
        },
        common_ports=[3000, 8080],
        endpoints=["/api", "/graphql"],
        
        version_files={
            "package.json": r'"@nestjs/core":\s*"[^"]*(\d+\.\d+\.?\d*)',
        },
        
        weights={
            "package": 0.95,
            "file": 0.9,
            "process": 0.85,
        }
    ),
    
    Framework.SPRING_BOOT: FrameworkSignature(
        framework=Framework.SPRING_BOOT,
        language=Language.JAVA,
        display_name="Spring Boot",
        description="Java-based framework for microservices",
        
        file_patterns=[
            "pom.xml",
            "build.gradle",
            "application.properties",
            "application.yml",
        ],
        package_names=[
            "spring-boot-starter",
            "org.springframework.boot",
        ],
        env_var_keys=[
            "SPRING_PROFILES_ACTIVE",
            "JAVA_OPTS",
        ],
        process_patterns=[
            r"java.*spring-boot",
            r"java.*-jar.*\.jar",
        ],
        http_headers={},
        common_ports=[8080, 8443, 9090],
        endpoints=["/actuator/health", "/actuator/info"],
        
        version_files={
            "pom.xml": r'<spring-boot\.version>(\d+\.\d+\.?\d*)</spring-boot\.version>',
        },
        
        weights={
            "package": 0.95,
            "file": 0.9,
            "process": 0.85,
            "endpoint": 0.8,
        }
    ),
}


def get_framework_signature(framework: Framework) -> FrameworkSignature:
    """Get signature for a framework."""
    return FRAMEWORK_DATABASE.get(framework)


def get_all_frameworks() -> List[FrameworkSignature]:
    """Get all framework signatures."""
    return list(FRAMEWORK_DATABASE.values())


def search_frameworks(language: Language = None) -> List[FrameworkSignature]:
    """Search frameworks by language."""
    frameworks = get_all_frameworks()
    
    if language:
        frameworks = [f for f in frameworks if f.language == language]
    
    return frameworks

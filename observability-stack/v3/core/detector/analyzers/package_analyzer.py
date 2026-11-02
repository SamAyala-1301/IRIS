"""Package manager analysis for framework detection."""
import json
import re
from ..base import Framework, Language

class PackageAnalyzer:
    """Analyze package manager files for framework detection."""
    
    # Python packages (requirements.txt, Pipfile, pyproject.toml)
    PYTHON_PACKAGES = {
        'flask': Framework.FLASK,
        'Flask': Framework.FLASK,
        'django': Framework.DJANGO,
        'Django': Framework.DJANGO,
        'fastapi': Framework.FASTAPI,
        'FastAPI': Framework.FASTAPI,
    }
    
    # Node.js packages (package.json)
    NODEJS_PACKAGES = {
        'express': Framework.EXPRESS,
        '@nestjs/core': Framework.NESTJS,
        '@nestjs/common': Framework.NESTJS,
    }
    
    # Java packages (pom.xml, build.gradle)
    JAVA_PACKAGES = {
        'spring-boot-starter': Framework.SPRING_BOOT,
        'org.springframework.boot': Framework.SPRING_BOOT,
    }
    
    def analyze(self, container) -> dict:
        """Analyze package files in container."""
        hints = {}
        
        # Try Python package files
        hints.update(self._analyze_python(container))
        
        # Try Node.js package.json
        hints.update(self._analyze_nodejs(container))
        
        # Try Java build files
        hints.update(self._analyze_java(container))
        
        return hints
    
    def _analyze_python(self, container) -> dict:
        """Analyze Python package files."""
        hints = {}
        
        # Check requirements.txt
        try:
            result = container.exec_run("cat requirements.txt")
            if result.exit_code == 0:
                content = result.output.decode('utf-8', errors='ignore')
                
                for package, framework in self.PYTHON_PACKAGES.items():
                    if package in content:
                        hints[framework] = hints.get(framework, 0) + 0.7
                        
                        # Try to extract version
                        version_match = re.search(
                            f'{package}[=><]+([\\d.]+)', 
                            content, 
                            re.IGNORECASE
                        )
                        if version_match:
                            hints[f'{framework}_version'] = version_match.group(1)
        except Exception:
            pass
        
        # Check Pipfile
        try:
            result = container.exec_run("cat Pipfile")
            if result.exit_code == 0:
                content = result.output.decode('utf-8', errors='ignore')
                for package, framework in self.PYTHON_PACKAGES.items():
                    if package in content:
                        hints[framework] = hints.get(framework, 0) + 0.6
        except Exception:
            pass
        
        return hints
    
    def _analyze_nodejs(self, container) -> dict:
        """Analyze Node.js package.json."""
        hints = {}
        
        try:
            result = container.exec_run("cat package.json")
            if result.exit_code == 0:
                content = result.output.decode('utf-8', errors='ignore')
                
                # Try to parse as JSON
                try:
                    package_data = json.loads(content)
                    dependencies = {
                        **package_data.get('dependencies', {}),
                        **package_data.get('devDependencies', {})
                    }
                    
                    for package, framework in self.NODEJS_PACKAGES.items():
                        if package in dependencies:
                            hints[framework] = hints.get(framework, 0) + 0.8
                            version = dependencies[package]
                            hints[f'{framework}_version'] = version
                            
                except json.JSONDecodeError:
                    # Fallback to simple text search
                    for package, framework in self.NODEJS_PACKAGES.items():
                        if package in content:
                            hints[framework] = hints.get(framework, 0) + 0.6
        except Exception:
            pass
        
        return hints
    
    def _analyze_java(self, container) -> dict:
        """Analyze Java build files."""
        hints = {}
        
        # Check pom.xml (Maven)
        try:
            result = container.exec_run("cat pom.xml")
            if result.exit_code == 0:
                content = result.output.decode('utf-8', errors='ignore')
                
                for package, framework in self.JAVA_PACKAGES.items():
                    if package in content:
                        hints[framework] = hints.get(framework, 0) + 0.7
        except Exception:
            pass
        
        # Check build.gradle (Gradle)
        try:
            result = container.exec_run("cat build.gradle")
            if result.exit_code == 0:
                content = result.output.decode('utf-8', errors='ignore')
                
                for package, framework in self.JAVA_PACKAGES.items():
                    if package in content:
                        hints[framework] = hints.get(framework, 0) + 0.7
        except Exception:
            pass
        
        return hints
    
    def get_indicators(self) -> dict:
        """Get package indicators."""
        return {
            "python_packages": self.PYTHON_PACKAGES,
            "nodejs_packages": self.NODEJS_PACKAGES,
            "java_packages": self.JAVA_PACKAGES
        }

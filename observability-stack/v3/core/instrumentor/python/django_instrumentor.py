"""Django auto-instrumentation."""
from ..base import Instrumentor, InstrumentationResult, InstrumentationStatus
from ..otel_config import OTelConfigGenerator

class DjangoInstrumentor(Instrumentor):
    """Auto-instrument Django applications."""
    
    def __init__(self):
        self.config_gen = OTelConfigGenerator()
    
    def instrument(self, container, detection_result) -> InstrumentationResult:
        """
        Instrument Django container with OpenTelemetry.
        
        Strategy:
        1. Add OpenTelemetry packages to requirements.txt
        2. Create otel_init.py
        3. Modify manage.py or wsgi.py to import otel_init
        4. Update Django settings.py
        """
        modifications = []
        
        try:
            # 1. Update requirements.txt
            self._update_requirements(container)
            modifications.append("Added OpenTelemetry packages")
            
            # 2. Create otel_init.py
            service_name = f"{self.config_gen.service_name_prefix}-{container.name}"
            otel_code = self._generate_otel_code(service_name)
            self._create_otel_file(container, otel_code)
            modifications.append("Created otel_init.py")
            
            # 3. Modify manage.py
            self._modify_manage_py(container)
            modifications.append("Modified manage.py")
            
            # 4. Install packages
            self._install_packages(container)
            modifications.append("Installed packages")
            
            modifications.append("⚠️  Container restart required")
            
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="django",
                status=InstrumentationStatus.INSTRUMENTED,
                metrics_endpoint=f"http://localhost:9090/metrics",
                trace_endpoint=f"http://otel-collector:4317",
                modifications=modifications
            )
            
        except Exception as e:
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="django",
                status=InstrumentationStatus.FAILED,
                error_message=str(e),
                modifications=modifications
            )
    
    def _generate_otel_code(self, service_name: str) -> str:
        """Generate Django instrumentation code."""
        otel_init = self.config_gen.generate_python_otel_init("django", service_name)
        django_inst = self.config_gen.generate_django_instrumentation()
        return otel_init + "\n" + django_inst
    
    def _update_requirements(self, container):
        """Add OpenTelemetry packages to requirements.txt."""
        packages = self.config_gen.generate_requirements_additions("django")
        
        result = container.exec_run("cat requirements.txt")
        existing = result.output.decode('utf-8') if result.exit_code == 0 else ""
        
        new_requirements = existing.strip() + "\n\n# ObsStack OpenTelemetry\n"
        new_requirements += "\n".join(packages)
        
        container.exec_run(f"sh -c 'echo \"{new_requirements}\" > requirements.txt'")
    
    def _create_otel_file(self, container, code: str):
        """Create otel_init.py in container."""
        container.exec_run(f'sh -c "cat > otel_init.py << \'EOL\'\n{code}\nEOL"')
    
    def _modify_manage_py(self, container):
        """Modify manage.py to import otel_init."""
        result = container.exec_run("cat manage.py")
        if result.exit_code != 0:
            return
        
        code = result.output.decode('utf-8')
        
        if "otel_init" in code:
            return  # Already instrumented
        
        # Add import after shebang
        lines = code.split('\n')
        
        # Find main block
        for i, line in enumerate(lines):
            if 'if __name__' in line:
                lines.insert(i, "    import otel_init  # ObsStack")
                break
        
        modified = '\n'.join(lines)
        container.exec_run(f'sh -c "cat > manage.py << \'EOL\'\n{modified}\nEOL"')
    
    def _install_packages(self, container):
        """Install OpenTelemetry packages."""
        result = container.exec_run("pip install -r requirements.txt")
        if result.exit_code != 0:
            raise RuntimeError(f"Installation failed: {result.output.decode('utf-8')}")
    
    def verify_instrumentation(self, container) -> bool:
        """Verify instrumentation."""
        result = container.exec_run("test -f otel_init.py")
        if result.exit_code != 0:
            return False
        
        result = container.exec_run("pip show opentelemetry-api")
        return result.exit_code == 0
    
    def rollback(self, container) -> bool:
        """Rollback changes."""
        try:
            container.exec_run("rm -f otel_init.py")
            return True
        except Exception:
            return False
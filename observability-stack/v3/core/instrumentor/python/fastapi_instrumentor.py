"""FastAPI auto-instrumentation."""
from ..base import Instrumentor, InstrumentationResult, InstrumentationStatus
from ..otel_config import OTelConfigGenerator

class FastAPIInstrumentor(Instrumentor):
    """Auto-instrument FastAPI applications."""
    
    def __init__(self):
        self.config_gen = OTelConfigGenerator()
    
    def instrument(self, container, detection_result) -> InstrumentationResult:
        """Instrument FastAPI container."""
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
            
            # 3. Modify main.py
            self._modify_main_file(container)
            modifications.append("Modified main.py")
            
            # 4. Install packages
            self._install_packages(container)
            modifications.append("Installed packages")
            
            modifications.append("⚠️  Container restart required")
            
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="fastapi",
                status=InstrumentationStatus.INSTRUMENTED,
                metrics_endpoint=f"http://localhost:9090/metrics",
                trace_endpoint=f"http://otel-collector:4317",
                modifications=modifications
            )
            
        except Exception as e:
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="fastapi",
                status=InstrumentationStatus.FAILED,
                error_message=str(e),
                modifications=modifications
            )
    
    def _generate_otel_code(self, service_name: str) -> str:
        """Generate FastAPI instrumentation code."""
        otel_init = self.config_gen.generate_python_otel_init("fastapi", service_name)
        fastapi_inst = self.config_gen.generate_fastapi_instrumentation()
        return otel_init + "\n" + fastapi_inst
    
    def _update_requirements(self, container):
        """Add OpenTelemetry packages."""
        packages = self.config_gen.generate_requirements_additions("fastapi")
        
        result = container.exec_run("cat requirements.txt")
        existing = result.output.decode('utf-8') if result.exit_code == 0 else ""
        
        new_requirements = existing.strip() + "\n\n# ObsStack OpenTelemetry\n"
        new_requirements += "\n".join(packages)
        
        container.exec_run(f"sh -c 'echo \"{new_requirements}\" > requirements.txt'")
    
    def _create_otel_file(self, container, code: str):
        """Create otel_init.py."""
        container.exec_run(f'sh -c "cat > otel_init.py << \'EOL\'\n{code}\nEOL"')
    
    def _modify_main_file(self, container):
        """Modify main.py or app.py."""
        # Try main.py first, then app.py
        for filename in ["main.py", "app.py"]:
            result = container.exec_run(f"cat {filename}")
            if result.exit_code == 0:
                code = result.output.decode('utf-8')
                
                if "otel_init" in code:
                    return  # Already instrumented
                
                lines = code.split('\n')
                
                # Add import at top
                first_import = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        first_import = i
                        break
                
                lines.insert(first_import, "import otel_init  # ObsStack")
                
                # Find FastAPI app creation
                for i, line in enumerate(lines):
                    if "FastAPI()" in line:
                        indent = len(line) - len(line.lstrip())
                        lines.insert(i + 1, " " * indent + "app = otel_init.instrument_fastapi_app(app)")
                        break
                
                modified = '\n'.join(lines)
                container.exec_run(f'sh -c "cat > {filename} << \'EOL\'\n{modified}\nEOL"')
                return
    
    def _install_packages(self, container):
        """Install packages."""
        result = container.exec_run("pip install -r requirements.txt")
        if result.exit_code != 0:
            raise RuntimeError(f"Installation failed: {result.output.decode('utf-8')}")
    
    def verify_instrumentation(self, container) -> bool:
        """Verify instrumentation."""
        result = container.exec_run("test -f otel_init.py")
        return result.exit_code == 0
    
    def rollback(self, container) -> bool:
        """Rollback changes."""
        try:
            container.exec_run("rm -f otel_init.py")
            return True
        except Exception:
            return False
"""Flask auto-instrumentation."""
import os
import tempfile
from ..base import Instrumentor, InstrumentationResult, InstrumentationStatus
from ..otel_config import OTelConfigGenerator

class FlaskInstrumentor(Instrumentor):
    """Auto-instrument Flask applications."""
    
    def __init__(self):
        self.config_gen = OTelConfigGenerator()
    
    def instrument(self, container, detection_result) -> InstrumentationResult:
        """
        Instrument Flask container with OpenTelemetry.
        
        Strategy:
        1. Add OpenTelemetry packages to requirements.txt
        2. Create otel_init.py file
        3. Modify app.py to import otel_init
        4. Restart container
        """
        modifications = []
        
        try:
            # 1. Update requirements.txt
            self._update_requirements(container)
            modifications.append("Added OpenTelemetry packages to requirements.txt")
            
            # 2. Create otel_init.py
            service_name = f"{self.config_gen.service_name_prefix}-{container.name}"
            otel_code = self._generate_otel_code(service_name)
            self._create_otel_file(container, otel_code)
            modifications.append("Created otel_init.py")
            
            # 3. Modify app.py to import otel_init
            self._modify_app_file(container)
            modifications.append("Modified app.py to import OpenTelemetry")
            
            # 4. Install packages
            self._install_packages(container)
            modifications.append("Installed OpenTelemetry packages")
            
            # 5. Restart app (container must be restarted by user)
            modifications.append("⚠️  Container restart required")
            
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="flask",
                status=InstrumentationStatus.INSTRUMENTED,
                metrics_endpoint=f"http://localhost:9090/metrics",
                trace_endpoint=f"http://otel-collector:4317",
                modifications=modifications
            )
            
        except Exception as e:
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="flask",
                status=InstrumentationStatus.FAILED,
                error_message=str(e),
                modifications=modifications
            )
    
    def _generate_otel_code(self, service_name: str) -> str:
        """Generate complete Flask instrumentation code."""
        otel_init = self.config_gen.generate_python_otel_init("flask", service_name)
        flask_inst = self.config_gen.generate_flask_instrumentation()
        return otel_init + "\n" + flask_inst
    
    def _update_requirements(self, container):
        """Add OpenTelemetry packages to requirements.txt."""
        packages = self.config_gen.generate_requirements_additions("flask")
        
        # Read existing requirements
        result = container.exec_run("cat requirements.txt")
        existing = result.output.decode('utf-8') if result.exit_code == 0 else ""
        
        # Add new packages
        new_requirements = existing.strip() + "\n\n# ObsStack OpenTelemetry\n"
        new_requirements += "\n".join(packages)
        
        # Write back
        container.exec_run(f"sh -c 'echo \"{new_requirements}\" > requirements.txt'")
    
    def _create_otel_file(self, container, code: str):
        """Create otel_init.py in container."""
        # Escape quotes for shell
        code_escaped = code.replace('"', '\\"').replace("'", "\\'")
        container.exec_run(f'sh -c "cat > otel_init.py << \'EOL\'\n{code}\nEOL"')
    
    def _modify_app_file(self, container):
        """Modify app.py to import and use otel_init."""
        # Read app.py
        result = container.exec_run("cat app.py")
        if result.exit_code != 0:
            raise RuntimeError("Could not read app.py")
        
        app_code = result.output.decode('utf-8')
        
        # Check if already instrumented
        if "otel_init" in app_code:
            return  # Already instrumented
        
        # Add import at the top
        lines = app_code.split('\n')
        
        # Find first import line
        first_import = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                first_import = i
                break
        
        # Insert otel_init import
        lines.insert(first_import, "import otel_init  # ObsStack instrumentation")
        
        # Find Flask app creation
        for i, line in enumerate(lines):
            if "Flask(__name__)" in line:
                # Add instrumentation call after app creation
                indent = len(line) - len(line.lstrip())
                lines.insert(i + 1, " " * indent + "app = otel_init.instrument_flask_app(app)")
                break
        
        modified_code = '\n'.join(lines)
        
        # Write back
        container.exec_run(f'sh -c "cat > app.py << \'EOL\'\n{modified_code}\nEOL"')
    
    def _install_packages(self, container):
        """Install OpenTelemetry packages."""
        result = container.exec_run("pip install -r requirements.txt")
        if result.exit_code != 0:
            raise RuntimeError(f"Package installation failed: {result.output.decode('utf-8')}")
    
    def verify_instrumentation(self, container) -> bool:
        """Verify Flask instrumentation is working."""
        # Check if otel_init.py exists
        result = container.exec_run("test -f otel_init.py")
        if result.exit_code != 0:
            return False
        
        # Check if packages are installed
        result = container.exec_run("pip show opentelemetry-api")
        return result.exit_code == 0
    
    def rollback(self, container) -> bool:
        """Rollback instrumentation changes."""
        try:
            # Remove otel_init.py
            container.exec_run("rm -f otel_init.py")
            
            # Remove OTel packages from requirements.txt
            result = container.exec_run("cat requirements.txt")
            if result.exit_code == 0:
                requirements = result.output.decode('utf-8')
                lines = [l for l in requirements.split('\n') 
                        if 'opentelemetry' not in l.lower() and 'obsstack' not in l.lower()]
                new_req = '\n'.join(lines)
                container.exec_run(f'sh -c "echo \\"{new_req}\\" > requirements.txt"')
            
            return True
        except Exception:
            return False
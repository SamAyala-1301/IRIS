"""Express.js auto-instrumentation."""
import json
from ..base import Instrumentor, InstrumentationResult, InstrumentationStatus
from ..otel_config import OTelConfigGenerator

class ExpressInstrumentor(Instrumentor):
    """Auto-instrument Express applications."""
    
    def __init__(self):
        self.config_gen = OTelConfigGenerator()
    
    def instrument(self, container, detection_result) -> InstrumentationResult:
        """Instrument Express container."""
        modifications = []
        
        try:
            # 1. Update package.json
            self._update_package_json(container)
            modifications.append("Updated package.json")
            
            # 2. Create otel.js
            service_name = f"{self.config_gen.service_name_prefix}-{container.name}"
            otel_code = self.config_gen.generate_nodejs_otel_init("express", service_name)
            self._create_otel_file(container, otel_code)
            modifications.append("Created otel.js")
            
            # 3. Modify app.js or server.js
            self._modify_app_file(container)
            modifications.append("Modified app entry point")
            
            # 4. Install packages
            self._install_packages(container)
            modifications.append("Installed OpenTelemetry packages")
            
            modifications.append("⚠️  Container restart required")
            
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="express",
                status=InstrumentationStatus.INSTRUMENTED,
                metrics_endpoint=f"http://localhost:9090/metrics",
                trace_endpoint=f"http://otel-collector:4317",
                modifications=modifications
            )
            
        except Exception as e:
            return InstrumentationResult(
                container_id=container.id,
                container_name=container.name,
                framework="express",
                status=InstrumentationStatus.FAILED,
                error_message=str(e),
                modifications=modifications
            )
    
    def _update_package_json(self, container):
        """Add OpenTelemetry packages to package.json."""
        # Read existing package.json
        result = container.exec_run("cat package.json")
        if result.exit_code != 0:
            raise RuntimeError("Could not read package.json")
        
        package_data = json.loads(result.output.decode('utf-8'))
        
        # Add OpenTelemetry dependencies
        new_deps = self.config_gen.generate_package_json_additions("express")
        
        if "dependencies" not in package_data:
            package_data["dependencies"] = {}
        
        package_data["dependencies"].update(new_deps)
        
        # Write back
        new_package_json = json.dumps(package_data, indent=2)
        container.exec_run(f'sh -c "cat > package.json << \'EOL\'\n{new_package_json}\nEOL"')
    
    def _create_otel_file(self, container, code: str):
        """Create otel.js in container."""
        container.exec_run(f'sh -c "cat > otel.js << \'EOL\'\n{code}\nEOL"')
    
    def _modify_app_file(self, container):
        """Modify app.js or server.js to require otel.js."""
        # Try app.js first, then server.js
        for filename in ["app.js", "server.js", "index.js"]:
            result = container.exec_run(f"cat {filename}")
            if result.exit_code == 0:
                code = result.output.decode('utf-8')
                
                if "otel.js" in code:
                    return  # Already instrumented
                
                # Add require at the very top
                modified = "// ObsStack OpenTelemetry\nrequire('./otel.js');\n\n" + code
                
                container.exec_run(f'sh -c "cat > {filename} << \'EOL\'\n{modified}\nEOL"')
                return
    
    def _install_packages(self, container):
        """Install npm packages."""
        result = container.exec_run("npm install")
        if result.exit_code != 0:
            raise RuntimeError(f"npm install failed: {result.output.decode('utf-8')}")
    
    def verify_instrumentation(self, container) -> bool:
        """Verify instrumentation."""
        result = container.exec_run("test -f otel.js")
        return result.exit_code == 0
    
    def rollback(self, container) -> bool:
        """Rollback changes."""
        try:
            container.exec_run("rm -f otel.js")
            return True
        except Exception:
            return False
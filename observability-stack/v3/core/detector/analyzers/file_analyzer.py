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

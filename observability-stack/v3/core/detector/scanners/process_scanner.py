"""Process scanning for runtime detection - FIXED."""
from ..base import Framework, Language
import re

class ProcessScanner:
    """Scan running processes to detect framework."""
    
    PROCESS_PATTERNS = {
        # Python frameworks - MORE FLEXIBLE PATTERNS
        r'python.*app\.py': (Framework.FLASK, Language.PYTHON),
        r'python.*manage\.py': (Framework.DJANGO, Language.PYTHON),
        r'python.*main\.py': (Framework.FASTAPI, Language.PYTHON),
        r'python': (Framework.FLASK, Language.PYTHON),  # Generic Python fallback
        r'gunicorn': (Framework.FLASK, Language.PYTHON),
        r'uvicorn': (Framework.FASTAPI, Language.PYTHON),
        
        # Node.js frameworks
        r'node.*app\.js': (Framework.EXPRESS, Language.NODEJS),
        r'node.*server\.js': (Framework.EXPRESS, Language.NODEJS),
        r'node': (Framework.EXPRESS, Language.NODEJS),  # Generic Node fallback
        r'npm': (Framework.EXPRESS, Language.NODEJS),
        
        # Java frameworks
        r'java.*\.jar': (Framework.SPRING_BOOT, Language.JAVA),
        r'java': (Framework.SPRING_BOOT, Language.JAVA),
    }
    
    def scan(self, container) -> dict:
        """Scan container processes."""
        hints = {}
        
        try:
            # Get running processes - MORE ROBUST
            exec_result = container.exec_run("ps aux", stderr=False)
            
            if exec_result.exit_code == 0:
                processes = exec_result.output.decode('utf-8', errors='ignore')
                
                # Check each process pattern
                for pattern, (framework, language) in self.PROCESS_PATTERNS.items():
                    if re.search(pattern, processes, re.IGNORECASE | re.MULTILINE):
                        # Give higher score to more specific patterns
                        score = 0.8 if '.*' in pattern else 0.6
                        hints[framework] = max(hints.get(framework, 0), score)
                        break  # Stop at first match to avoid double-counting
                        
        except Exception as e:
            # Silently fail - some containers don't have ps
            pass
        
        return hints
    
    def get_indicators(self) -> dict:
        """Get process indicators."""
        return {"process_patterns": self.PROCESS_PATTERNS}
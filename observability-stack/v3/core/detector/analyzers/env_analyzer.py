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

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
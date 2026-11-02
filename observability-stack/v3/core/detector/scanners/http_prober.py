"""HTTP probing for framework fingerprinting - FIXED."""
import requests
from typing import Optional, Tuple
from ..base import Framework

class HTTPProber:
    """Probe containers via HTTP to detect frameworks."""
    
    HEADER_PATTERNS = {
        'Server': {
            'Werkzeug': Framework.FLASK,
            'gunicorn': Framework.FLASK,
            'uvicorn': Framework.FASTAPI,
        },
        'X-Powered-By': {
            'Express': Framework.EXPRESS,
        }
    }
    
    ENDPOINT_PATTERNS = {
        '/admin/': Framework.DJANGO,
        '/docs': Framework.FASTAPI,
        '/actuator/health': Framework.SPRING_BOOT,
    }
    
    def probe(self, container) -> dict:
        """
        Probe container HTTP endpoints.
        FIXED: Try multiple connection methods.
        """
        hints = {}
        
        try:
            # METHOD 1: Try container IP
            container_ip = self._get_container_ip(container)
            if container_ip:
                hints.update(self._probe_ip(container_ip))
            
            # METHOD 2: Try localhost with port mappings
            if not hints:
                port_mappings = self._get_port_mappings(container)
                for host_port in port_mappings:
                    hints.update(self._probe_localhost(host_port))
                    if hints:
                        break
        
        except Exception as e:
            # Silently fail - HTTP probing is optional
            pass
        
        return hints
    
    def _probe_ip(self, ip: str, ports: list = [5000, 8000, 3000, 8080]) -> dict:
        """Probe container by IP."""
        hints = {}
        
        for port in ports:
            try:
                response = requests.get(
                    f"http://{ip}:{port}",
                    timeout=2,
                    allow_redirects=False
                )
                
                # Analyze headers
                hints.update(self._analyze_headers(response.headers))
                
                if hints:
                    break  # Found something, stop
                    
            except requests.exceptions.RequestException:
                continue
        
        return hints
    
    def _probe_localhost(self, port: int) -> dict:
        """Probe container via localhost port mapping."""
        hints = {}
        
        try:
            response = requests.get(
                f"http://localhost:{port}",
                timeout=2,
                allow_redirects=False
            )
            
            hints.update(self._analyze_headers(response.headers))
            
        except requests.exceptions.RequestException:
            pass
        
        return hints
    
    def _get_container_ip(self, container) -> Optional[str]:
        """Get container's IP address."""
        try:
            networks = container.attrs['NetworkSettings']['Networks']
            for network in networks.values():
                if network.get('IPAddress'):
                    return network['IPAddress']
        except Exception:
            pass
        return None
    
    def _get_port_mappings(self, container) -> list:
        """Get list of host port mappings."""
        ports = []
        try:
            port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            for port_key, bindings in port_bindings.items():
                if bindings:
                    for binding in bindings:
                        host_port = binding.get('HostPort')
                        if host_port:
                            ports.append(int(host_port))
        except Exception:
            pass
        
        return ports
    
    def _analyze_headers(self, headers) -> dict:
        """Analyze HTTP headers for framework hints."""
        hints = {}
        
        for header_name, patterns in self.HEADER_PATTERNS.items():
            header_value = headers.get(header_name, '')
            
            for pattern, framework in patterns.items():
                if pattern.lower() in header_value.lower():
                    hints[framework] = 0.6  # Increased from 0.5
        
        return hints
    
    def get_indicators(self) -> dict:
        """Get HTTP probing indicators."""
        return {
            "header_patterns": self.HEADER_PATTERNS,
            "endpoint_patterns": self.ENDPOINT_PATTERNS
        }


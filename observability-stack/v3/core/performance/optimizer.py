"""Performance optimization utilities."""
import psutil
from typing import Dict, List, Tuple

class PerformanceOptimizer:
    """Optimize ObsStack performance based on system resources."""
    
    def __init__(self):
        self.system_memory = psutil.virtual_memory().total
        self.cpu_count = psutil.cpu_count()
    
    def get_recommended_config(self) -> Dict:
        """
        Get recommended configuration based on system resources.
        
        Returns:
            Dict with optimized settings
        """
        memory_gb = self.system_memory / (1024 ** 3)
        
        return {
            'prometheus': self._optimize_prometheus(memory_gb),
            'otel_collector': self._optimize_otel_collector(memory_gb),
            'grafana': self._optimize_grafana(memory_gb),
            'system': self._get_system_limits(memory_gb),
        }
    
    def _optimize_prometheus(self, memory_gb: float) -> Dict:
        """Optimize Prometheus configuration."""
        # Allocate 20-30% of memory to Prometheus
        prometheus_memory = int(memory_gb * 0.25)
        
        config = {
            'memory_limit': f'{prometheus_memory}g',
            'storage_retention': '15d' if memory_gb > 8 else '7d',
            'scrape_interval': '15s' if memory_gb > 4 else '30s',
            'query_timeout': '2m',
            'query_max_concurrency': min(20, self.cpu_count * 2),
        }
        
        return config
    
    def _optimize_otel_collector(self, memory_gb: float) -> Dict:
        """Optimize OTEL Collector configuration."""
        # Allocate 10-15% of memory
        otel_memory = int(memory_gb * 0.15 * 1024)  # MB
        
        config = {
            'memory_limit_mib': otel_memory,
            'batch_size': 2048 if memory_gb > 8 else 1024,
            'batch_timeout': '10s',
            'queue_size': 5000 if memory_gb > 8 else 2000,
        }
        
        return config
    
    def _optimize_grafana(self, memory_gb: float) -> Dict:
        """Optimize Grafana configuration."""
        config = {
            'memory_limit': f'{int(memory_gb * 0.1)}g',
            'dashboard_cache': True if memory_gb > 4 else False,
            'concurrent_render_limit': min(5, self.cpu_count),
        }
        
        return config
    
    def _get_system_limits(self, memory_gb: float) -> Dict:
        """Get recommended system limits."""
        return {
            'max_containers': 20 if memory_gb > 16 else 10,
            'max_metrics_series': 1000000 if memory_gb > 16 else 500000,
            'recommended_min_memory_gb': 4,
            'current_memory_gb': round(memory_gb, 1),
            'cpu_cores': self.cpu_count,
        }
    
    def check_system_requirements(self) -> Tuple[bool, List[str]]:
        """
        Check if system meets minimum requirements.
        
        Returns:
            Tuple of (meets_requirements, list_of_warnings)
        """
        warnings = []
        memory_gb = self.system_memory / (1024 ** 3)
        
        # Check memory
        if memory_gb < 4:
            warnings.append(f"Low memory: {memory_gb:.1f}GB (recommended: 4GB+)")
        
        # Check CPU
        if self.cpu_count < 2:
            warnings.append(f"Low CPU cores: {self.cpu_count} (recommended: 2+)")
        
        # Check disk
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        if free_gb < 10:
            warnings.append(f"Low disk space: {free_gb:.1f}GB free (recommended: 10GB+)")
        
        meets_requirements = len(warnings) == 0
        return meets_requirements, warnings
    
    def generate_optimized_compose(self) -> Dict:
        """Generate optimized docker-compose configuration."""
        config = self.get_recommended_config()
        
        return {
            'services': {
                'prometheus': {
                    'deploy': {
                        'resources': {
                            'limits': {
                                'memory': config['prometheus']['memory_limit'],
                                'cpus': str(min(2.0, self.cpu_count * 0.5))
                            }
                        }
                    }
                },
                'otel-collector': {
                    'deploy': {
                        'resources': {
                            'limits': {
                                'memory': f"{config['otel_collector']['memory_limit_mib']}m",
                                'cpus': '1.0'
                            }
                        }
                    }
                },
                'grafana': {
                    'deploy': {
                        'resources': {
                            'limits': {
                                'memory': config['grafana']['memory_limit'],
                                'cpus': '0.5'
                            }
                        }
                    }
                }
            }
        }